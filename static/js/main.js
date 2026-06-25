document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const form = document.getElementById('research-form');
    const topicInput = document.getElementById('topic');
    const maxSubquestionsInput = document.getElementById('max-subquestions');
    const topKInput = document.getElementById('top-k');
    const startBtn = document.getElementById('start-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    
    const progressContainer = document.getElementById('progress-container');
    const currentAction = document.getElementById('current-action');
    const emptyState = document.getElementById('empty-state');
    const resultsContainer = document.getElementById('results-container');
    
    // Steps
    const stepScan = document.getElementById('step-scan');
    const stepPlan = document.getElementById('step-plan');
    const stepProcess = document.getElementById('step-process');
    const stepCompile = document.getElementById('step-compile');
    
    // Step Descriptions
    const scanDesc = document.getElementById('scan-desc');
    const planDesc = document.getElementById('plan-desc');
    const processDesc = document.getElementById('process-desc');
    const compileDesc = document.getElementById('compile-desc');
    
    const plannedSubquestionsList = document.getElementById('planned-subquestions-list');
    const loopProgressContainer = document.getElementById('loop-progress-container');
    const loopProgressFill = document.getElementById('loop-progress-fill');
    const loopProgressText = document.getElementById('loop-progress-text');
    
    // Tabs
    const tabReport = document.getElementById('tab-report');
    const tabEvidence = document.getElementById('tab-evidence');
    const contentReport = document.getElementById('content-report');
    const contentEvidence = document.getElementById('content-evidence');
    
    // Outputs
    const reportRendered = document.getElementById('report-rendered');
    const evidenceAccordion = document.getElementById('evidence-accordion');
    const copyReportBtn = document.getElementById('copy-report-btn');
    
    let eventSource = null;
    let totalQuestions = 0;
    let rawMarkdownReport = '';

    // Tab Switching Logic
    tabReport.addEventListener('click', () => {
        tabReport.classList.add('active');
        tabEvidence.classList.remove('active');
        contentReport.classList.remove('hidden');
        contentEvidence.classList.add('hidden');
    });

    tabEvidence.addEventListener('click', () => {
        tabEvidence.classList.add('active');
        tabReport.classList.remove('active');
        contentEvidence.classList.remove('hidden');
        contentReport.classList.add('hidden');
    });

    // Copy to Clipboard
    copyReportBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(rawMarkdownReport).then(() => {
            const originalText = copyReportBtn.innerHTML;
            copyReportBtn.innerHTML = '<i data-lucide="check" class="btn-icon"></i> Copied!';
            lucide.createIcons();
            setTimeout(() => {
                copyReportBtn.innerHTML = originalText;
                lucide.createIcons();
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    });

    // Form Submit
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const topic = topicInput.value.trim();
        const maxSubquestions = maxSubquestionsInput.value;
        const topK = topKInput.value;
        
        if (!topic) return;

        // Reset UI states
        resetUI();
        
        // Show progress and hide empty/results cards
        emptyState.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        progressContainer.classList.remove('hidden');
        
        startBtn.disabled = true;
        startBtn.classList.add('hidden');
        cancelBtn.classList.remove('hidden');
        
        // Build URL
        const url = `/api/research/stream?topic=${encodeURIComponent(topic)}&max_subquestions=${maxSubquestions}&top_k=${topK}`;
        
        // Initialize EventSource
        eventSource = new EventSource(url);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleAgentStep(data);
        };
        
        eventSource.onerror = (err) => {
            console.error('EventSource failed:', err);
            handleError('Connection lost or server error occurred.');
            closeConnection();
        };
    });

    // Cancel Button
    cancelBtn.addEventListener('click', () => {
        handleError('Research cancelled by user.');
        closeConnection();
    });

    function resetUI() {
        // Clear previous outputs
        reportRendered.innerHTML = '';
        evidenceAccordion.innerHTML = '';
        plannedSubquestionsList.innerHTML = '';
        plannedSubquestionsList.classList.add('hidden');
        loopProgressContainer.classList.add('hidden');
        loopProgressFill.style.width = '0%';
        loopProgressText.textContent = '0/0 completed';
        rawMarkdownReport = '';
        totalQuestions = 0;
        
        // Reset steps classes
        const steps = [stepScan, stepPlan, stepProcess, stepCompile];
        steps.forEach(step => {
            step.classList.remove('active', 'completed');
        });
        
        // Reset step descs
        scanDesc.textContent = 'Waiting...';
        planDesc.textContent = 'Waiting...';
        processDesc.textContent = 'Waiting...';
        compileDesc.textContent = 'Waiting...';
        
        currentAction.textContent = 'Initializing...';
        currentAction.style.background = '';
    }

    function closeConnection() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        startBtn.disabled = false;
        startBtn.classList.remove('hidden');
        cancelBtn.classList.add('hidden');
    }

    function handleError(msg) {
        currentAction.textContent = 'Error';
        currentAction.style.background = 'rgba(239, 68, 68, 0.2)';
        currentAction.style.color = '#f87171';
        
        // Set active step to error/muted
        const activeStep = document.querySelector('.step.active');
        if (activeStep) {
            activeStep.querySelector('p').textContent = msg;
        }
    }

    function handleAgentStep(data) {
        switch(data.status) {
            case 'loading_docs':
                currentAction.textContent = 'Scanning Documents';
                stepScan.classList.add('active');
                scanDesc.textContent = data.message;
                break;
                
            case 'loaded_docs':
                stepScan.classList.remove('active');
                stepScan.classList.add('completed');
                scanDesc.textContent = data.message;
                break;
                
            case 'planning':
                currentAction.textContent = 'Planning Sub-questions';
                stepPlan.classList.add('active');
                planDesc.textContent = data.message;
                break;
                
            case 'planned':
                stepPlan.classList.remove('active');
                stepPlan.classList.add('completed');
                planDesc.textContent = `Generated ${data.subquestions.length} focused sub-questions.`;
                
                // Show subquestions in step plan details
                totalQuestions = data.subquestions.length;
                plannedSubquestionsList.innerHTML = data.subquestions.map((q, idx) => `
                    <div class="subquestion-item">
                        <i data-lucide="circle-dot"></i>
                        <span>Q${idx+1}: ${q}</span>
                    </div>
                `).join('');
                plannedSubquestionsList.classList.remove('hidden');
                lucide.createIcons();
                
                // Set process active
                stepProcess.classList.add('active');
                loopProgressContainer.classList.remove('hidden');
                loopProgressText.textContent = `0/${totalQuestions} completed`;
                break;
                
            case 'searching':
                currentAction.textContent = `Retrieving Q${data.index + 1}`;
                processDesc.textContent = data.message;
                break;
                
            case 'synthesizing':
                currentAction.textContent = `Answering Q${data.index + 1}`;
                processDesc.textContent = data.message;
                break;
                
            case 'answered':
                const numCompleted = data.index + 1;
                const percentage = (numCompleted / totalQuestions) * 100;
                loopProgressFill.style.width = `${percentage}%`;
                loopProgressText.textContent = `${numCompleted}/${totalQuestions} completed`;
                break;
                
            case 'compiling':
                currentAction.textContent = 'Compiling Report';
                stepProcess.classList.remove('active');
                stepProcess.classList.add('completed');
                processDesc.textContent = 'Completed retrieval and synthesis loop.';
                
                stepCompile.classList.add('active');
                compileDesc.textContent = data.message;
                break;
                
            case 'done':
                stepCompile.classList.remove('active');
                stepCompile.classList.add('completed');
                compileDesc.textContent = 'Report compiled and exported successfully!';
                
                currentAction.textContent = 'Research Completed';
                currentAction.style.background = 'rgba(16, 185, 129, 0.15)';
                currentAction.style.color = '#34d399';
                
                // Render report & evidence
                rawMarkdownReport = data.report;
                reportRendered.innerHTML = marked.parse(data.report);
                
                renderEvidence(data.evidence);
                
                // Hide progress, show results
                progressContainer.classList.add('hidden');
                resultsContainer.classList.remove('hidden');
                
                // Trigger layout refresh for lucide icons
                lucide.createIcons();
                
                closeConnection();
                break;
                
            case 'error':
                handleError(data.message);
                closeConnection();
                break;
        }
    }

    function renderEvidence(evidenceMap) {
        evidenceAccordion.innerHTML = '';
        
        let index = 1;
        for (const [question, snippets] of Object.entries(evidenceMap)) {
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            
            // Header
            const header = document.createElement('div');
            header.className = 'accordion-header';
            header.innerHTML = `
                <h3>Q${index}: ${question}</h3>
                <i data-lucide="chevron-down" class="chevron-icon"></i>
            `;
            
            // Content
            const content = document.createElement('div');
            content.className = 'accordion-content';
            
            const snippetsContainer = document.createElement('div');
            snippetsContainer.className = 'evidence-snippets';
            
            if (snippets.length === 0) {
                snippetsContainer.innerHTML = `<p class="snippet-text">No evidence snippets were retrieved for this sub-question.</p>`;
            } else {
                snippets.forEach(snippet => {
                    // Extract relative file path
                    const filename = snippet.file.replace(/\\/g, '/').split('/').pop();
                    
                    const snippetCard = document.createElement('div');
                    snippetCard.className = 'snippet-card';
                    snippetCard.innerHTML = `
                        <div class="snippet-meta">
                            <span class="meta-file"><i data-lucide="file" class="btn-icon" style="width:0.8rem;height:0.8rem;display:inline;vertical-align:-1px;"></i> ${filename}</span>
                            <span class="meta-score">Match Score: ${snippet.score}</span>
                        </div>
                        <p class="snippet-text">${escapeHtml(snippet.snippet)}</p>
                    `;
                    snippetsContainer.appendChild(snippetCard);
                });
            }
            
            content.appendChild(snippetsContainer);
            accordionItem.appendChild(header);
            accordionItem.appendChild(content);
            
            // Toggle event
            header.addEventListener('click', () => {
                accordionItem.classList.toggle('open');
            });
            
            evidenceAccordion.appendChild(accordionItem);
            index++;
        }
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
});
