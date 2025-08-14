// City Brain Frontend JavaScript
class CityBrainChat {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendButton = document.getElementById('sendButton');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.charCount = document.querySelector('.char-count');
        
        this.isLoading = false;
        this.currentStep = 0;
        
        // Modal API configuration
        this.modalAppName = 'city-brain-urban-planning';
        this.modalFunction = 'get_scenario_insights';
        
        this.initializeEventListeners();
        this.updateCharCount();
    }

    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key handling
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Dynamic textbox expansion
        this.userInput.addEventListener('input', () => {
            this.updateCharCount();
            this.adjustTextareaHeight();
        });
        
        // Focus handling
        this.userInput.addEventListener('focus', () => {
            this.userInput.parentElement.classList.add('focused');
        });
        
        this.userInput.addEventListener('blur', () => {
            this.userInput.parentElement.classList.remove('focused');
        });
    }

    updateCharCount() {
        const currentLength = this.userInput.value.length;
        const maxLength = this.userInput.maxLength;
        this.charCount.textContent = `${currentLength}/${maxLength}`;
        
        // Update send button state
        this.sendButton.disabled = currentLength === 0 || this.isLoading;
        
        // Update character count color
        if (currentLength > maxLength * 0.9) {
            this.charCount.style.color = '#e74c3c';
        } else if (currentLength > maxLength * 0.7) {
            this.charCount.style.color = '#f39c12';
        } else {
            this.charCount.style.color = '#6c757d';
        }
    }

    adjustTextareaHeight() {
        this.userInput.style.height = 'auto';
        const scrollHeight = this.userInput.scrollHeight;
        const maxHeight = 200; // max-height from CSS
        
        if (scrollHeight > maxHeight) {
            this.userInput.style.height = maxHeight + 'px';
            this.userInput.style.overflowY = 'auto';
        } else {
            this.userInput.style.height = scrollHeight + 'px';
            this.userInput.style.overflowY = 'hidden';
        }
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isLoading) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input and reset height
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        this.updateCharCount();
        
        // Show loading state
        this.showLoading();
        
        try {
            // Call Modal API
            const response = await this.callModalAPI(message);
            
            // Hide loading
            this.hideLoading();
            
            // Add AI response to chat - pass the full response object for structured display
            if (typeof response === 'string') {
                // If we got a simple string, display it directly
                this.addMessage(response, 'assistant');
            } else {
                // If we got a structured response, pass it through
                this.addMessage(response, 'assistant');
            }
            
        } catch (error) {
            console.error('Error calling Modal API:', error);
            this.hideLoading();
            this.addMessage(`Sorry, I encountered an error while processing your request: ${error.message}. Please try again or check if your Modal app is deployed.`, 'assistant');
        }
    }

    async callModalAPI(query) {
        try {
            console.log(`Calling Modal API: ${this.modalAppName}::${this.modalFunction}`);
            
            // Call the Modal function using the Modal CLI
            let response = await this.executeModalCommand(query);
            
            console.log('Modal API response received:', response);
            console.log('Response type:', typeof response);
            console.log('Response keys:', response ? Object.keys(response) : 'Response is null/undefined');
            
            // If backend returned raw_output (stdout not parsed), try to extract JSON here
            if (response && response.raw_output && typeof response.raw_output === 'string') {
                console.warn('Backend returned raw_output; attempting to parse JSON client-side');
                const parsed = this.extractJsonFromMixedOutput(response.raw_output);
                if (parsed) {
                    console.log('✓ Successfully parsed JSON from raw_output');
                    response = parsed;
                } else {
                    console.warn('Failed to parse JSON from raw_output; falling back to message');
                    return 'Analysis completed but no detailed response received. Please check the console for response structure.';
                }
            }
            
            // Also handle the case where the response itself is a JSON string
            if (typeof response === 'string') {
                const parsed = this.extractJsonFromMixedOutput(response);
                if (parsed) {
                    console.log('✓ Parsed JSON from string response');
                    response = parsed;
                }
            }
            
            // Extract the analysis from the response - simplified to just get full_analysis and model_used
            if (response && response.llm_analysis && response.llm_analysis.analysis && response.llm_analysis.analysis.full_analysis) {
                console.log('✓ Found full_analysis in llm_analysis.analysis');
                
                // Return a simple object with just the analysis text and model info
                return {
                    analysis_text: response.llm_analysis.analysis.full_analysis,
                    model_used: response.llm_analysis.analysis.model_used || 'Unknown Model',
                    full_response: response // Keep the full response for debugging
                };
            } else if (response && response.llm_analysis && response.llm_analysis.full_analysis) {
                // Fallback: direct access to full_analysis in llm_analysis
                console.log('✓ Found full_analysis directly in llm_analysis');
                
                return {
                    analysis_text: response.llm_analysis.full_analysis,
                    model_used: response.llm_analysis.model_used || 'Unknown Model',
                    full_response: response
                };
            } else {
                console.warn('No full_analysis found in response');
                console.log('Response structure:', response);
                
                if (response && response.llm_analysis) {
                    console.log('llm_analysis keys:', Object.keys(response.llm_analysis));
                    if (response.llm_analysis.analysis) {
                        console.log('llm_analysis.analysis keys:', Object.keys(response.llm_analysis.analysis));
                    }
                }
                
                return 'Analysis completed but no detailed response received. Please check the console for response structure.';
            }
            
        } catch (error) {
            console.error('Modal API call failed:', error);
            console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            throw new Error(`Failed to call Modal API: ${error.message}`);
        }
    }

    extractJsonFromMixedOutput(text) {
        try {
            // Quick path: exact JSON
            return JSON.parse(text);
        } catch (_) {
            // Find the first '{' and try progressively
            const firstBrace = text.indexOf('{');
            if (firstBrace === -1) return null;
            const candidate = text.slice(firstBrace);
            // Try full tail
            try { return JSON.parse(candidate); } catch (_) {}
            // Try trimming line by line from the end
            const lines = candidate.split('\n');
            for (let end = lines.length; end > 0; end--) {
                const chunk = lines.slice(0, end).join('\n');
                try { return JSON.parse(chunk); } catch (_) {}
            }
            return null;
        }
    }

    async executeModalCommand(query) {
        // For now, we'll use a proxy approach since we can't directly call Modal from the browser
        // In production, you'd set up a backend API that calls Modal
        
        // Option 1: Use a backend proxy (recommended for production)
        if (this.hasBackendProxy()) {
            return await this.callBackendProxy(query);
        }
        
        // Option 2: Use Modal's web endpoint if available
        if (this.hasModalWebEndpoint()) {
            return await this.callModalWebEndpoint(query);
        }
        
        // Option 3: Fallback to simulated response with instructions
        console.warn('No backend proxy or Modal web endpoint available. Using fallback response.');
        return this.getFallbackResponse(query);
    }

    async callBackendProxy(query) {
        try {
            const response = await fetch('http://localhost:5001/api/modal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    app: this.modalAppName,
                    function: this.modalFunction,
                    query: query
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            throw new Error(`Backend proxy error: ${error.message}`);
        }
    }

    async callModalWebEndpoint(query) {
        try {
            // If Modal provides a web endpoint, use it here
            const response = await fetch(`https://your-modal-endpoint.modal.run/${this.modalFunction}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            throw new Error(`Modal web endpoint error: ${error.message}`);
        }
    }

    hasBackendProxy() {
        // Check if we have a backend proxy available
        // You can set this up with a simple Flask/FastAPI server
        return true; // Changed to true since we now have a backend proxy
    }

    hasModalWebEndpoint() {
        // Check if Modal provides a web endpoint
        // This would be configured in your Modal deployment
        return false; // Change to true when you have a web endpoint
    }

    getFallbackResponse(query) {
        return `I understand you're asking about: "${query}"

Currently, I'm running in demo mode. To get real AI-powered urban planning analysis, you need to:

1. **Deploy your Modal app:**
   \`\`\`bash
   modal deploy citybrain/modal_app.py
   \`\`\`

2. **Set up a backend proxy** to call Modal from the browser, or
3. **Use Modal's web endpoints** if available

Once connected, I'll provide real analysis using:
• Llama 3 AI model
• NYC zoning data
• Traffic analysis
• Professional urban planning insights

For now, here's what I can help with:
• Zoning regulations and amendments
• Traffic impact analysis
• Urban development scenarios
• Infrastructure planning

Please deploy your Modal app and set up the connection to get full AI-powered analysis! 🏙️✨`;
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        if (sender === 'user') {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        } else {
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        // Handle different content types
        if (typeof content === 'string') {
            messageText.innerHTML = this.formatMessage(content);
        } else if (typeof content === 'object' && content.analysis_text) {
            // Display the simplified AI response structure
            messageText.innerHTML = this.formatSimpleAIResponse(content);
        } else {
            messageText.innerHTML = '<p>Error: Invalid response format</p>';
        }
        
        messageContent.appendChild(messageText);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    formatMessage(text) {
        // Simple markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```(.*?)```/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
    }

    formatSimpleAIResponse(response) {
        let html = '';
        
        // Add the main analysis text with proper formatting
        if (response.analysis_text) {
            html += `<div class="ai-analysis">`;
            html += `<h4>🤖 AI Analysis</h4>`;
            html += `<div class="analysis-content">${this.formatAnalysisText(response.analysis_text)}</div>`;
            
            // Add model info
            if (response.model_used) {
                html += `<div class="model-info"><small>Model: ${response.model_used}</small></div>`;
            }
            html += `</div>`;
        }
        
        return html;
    }

    formatAnalysisText(text) {
        // Format the analysis text with proper line breaks and bullet points
        return text
            .split('\n')
            .map(line => {
                line = line.trim();
                if (line.startsWith('1.') || line.startsWith('2.') || line.startsWith('3.') || line.startsWith('4.') || line.startsWith('5.')) {
                    // Format numbered lists
                    return `<div class="numbered-item">${line}</div>`;
                } else if (line.startsWith('•') || line.startsWith('-')) {
                    // Format bullet points
                    return `<div class="bullet-item">${line}</div>`;
                } else if (line.includes(':') && line.length < 100) {
                    // Format section headers
                    return `<h5 class="section-header">${line}</h5>`;
                } else if (line.length > 0) {
                    // Regular paragraph
                    return `<p>${line}</p>`;
                } else {
                    // Empty line - add spacing
                    return '<br>';
                }
            })
            .join('');
    }

    showLoading() {
        this.isLoading = true;
        this.loadingOverlay.classList.remove('hidden');
        this.sendButton.disabled = true;
        this.userInput.disabled = true;
        
        // Animate loading steps
        this.animateLoadingSteps();
    }

    hideLoading() {
        this.isLoading = false;
        this.loadingOverlay.classList.add('hidden');
        this.sendButton.disabled = false;
        this.userInput.disabled = false;
        this.userInput.focus();
        
        // Reset loading steps
        this.resetLoadingSteps();
    }

    animateLoadingSteps() {
        const steps = document.querySelectorAll('.loading-steps .step');
        this.currentStep = 0;
        
        const stepInterval = setInterval(() => {
            if (this.currentStep < steps.length) {
                // Remove active class from all steps
                steps.forEach(step => step.classList.remove('active'));
                
                // Add active class to current step
                if (steps[this.currentStep]) {
                    steps[this.currentStep].classList.add('active');
                }
                
                this.currentStep++;
            } else {
                clearInterval(stepInterval);
            }
        }, 1500);
    }

    resetLoadingSteps() {
        const steps = document.querySelectorAll('.loading-steps .step');
        steps.forEach(step => step.classList.remove('active'));
        if (steps[0]) {
            steps[0].classList.add('active');
        }
    }
}

// Initialize the chat when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new CityBrainChat();
});

// Add utility functions for Modal API integration
window.CityBrainAPI = {
    // Check if Modal app is deployed
    async checkModalStatus() {
        try {
            // This would check if your Modal app is accessible
            const response = await fetch('http://localhost:5001/api/modal/status');
            return response.json();
        } catch (error) {
            return { status: 'error', message: 'Modal app not accessible' };
        }
    },
    
    // Get deployment instructions
    getDeploymentInstructions() {
        return {
            steps: [
                'Deploy Modal app: modal deploy citybrain/modal_app.py',
                'Set up backend proxy or web endpoint',
                'Configure CORS and authentication',
                'Test the connection'
            ],
            commands: [
                'modal app list',
                'modal app status city-brain-urban-planning',
                'modal run citybrain/modal_app.py::get_scenario_insights --query "test"'
            ]
        };
    }
}; 