let leftWidth = 20;
let middleWidth = 40;
let isResizing = false;
let currentHandle = null;

// Resizable panels
const handle1 = document.getElementById('handle1');
const handle2 = document.getElementById('handle2');
const contentWrapper = document.querySelector('.content-wrapper');

// Track current state
let currentMindmapId = null;
let currentBlockId = null;
let currentGraphId = null;
let allMindmaps = [];
let currentGraphData = null;
let simulation = null;

// API Functions
async function fetchMindmaps() {
    try {
        const response = await fetch('/api/mindmaps');
        if (!response.ok) throw new Error('Failed to fetch mindmaps');
        const data = await response.json();
        return data.mindmaps;
    } catch (error) {
        console.error('Error fetching mindmaps:', error);
        return [];
    }
}

async function fetchGraphData(graphId) {
    try {
        const response = await fetch(`/api/mindmaps/${graphId}/graph`);
        if (!response.ok) throw new Error('Failed to fetch graph');
        return await response.json();
    } catch (error) {
        console.error('Error fetching graph:', error);
        return null;
    }
}

async function switchMindmap(graphId) {
    try {
        const response = await fetch(`/api/mindmaps/${graphId}/switch`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to switch mindmap');
        return await response.json();
    } catch (error) {
        console.error('Error switching mindmap:', error);
        return null;
    }
}

async function switchBlock(blockId) {
    try {
        const response = await fetch(`/api/blocks/${blockId}/switch`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to switch block');
        return await response.json();
    } catch (error) {
        console.error('Error switching block:', error);
        return null;
    }
}

async function fetchBlockMessages(blockId) {
    try {
        const response = await fetch(`/api/blocks/${blockId}/messages`);
        if (!response.ok) throw new Error('Failed to fetch messages');
        return await response.json();
    } catch (error) {
        console.error('Error fetching messages:', error);
        return null;
    }
}

// Generic chat API using ConversationManager (mirrors CLI logic)
async function chatWithAssistant(content) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        if (!response.ok) throw new Error('Failed to send chat message');
        return await response.json();
    } catch (error) {
        console.error('Error in chatWithAssistant:', error);
        return null;
    }
}

function startResize(e, handle) {
    isResizing = true;
    currentHandle = handle;
    e.preventDefault();
}

document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;

    const rect = contentWrapper.getBoundingClientRect();
    const totalWidth = rect.width;
    const mouseX = e.clientX - rect.left;
    const percentX = (mouseX / totalWidth) * 100;

    if (currentHandle === handle1) {
        leftWidth = Math.max(15, Math.min(40, percentX));
    } else if (currentHandle === handle2) {
        middleWidth = Math.max(20, Math.min(70, percentX - leftWidth));
    }

    updateLayout();
});

document.addEventListener('mouseup', () => {
    isResizing = false;
    currentHandle = null;
});

function updateLayout() {
    const leftPanel = document.querySelector('.left-panel');
    const middlePanel = document.querySelector('.middle-panel');
    const rightPanel = document.querySelector('.right-panel');

    leftPanel.style.flex = `0 0 ${leftWidth}%`;
    middlePanel.style.flex = `0 0 ${middleWidth}%`;
    rightPanel.style.flex = `1`;
    
    // Redraw mindmap on resize
    if (simulation) {
        drawMindmap(currentMindmapId);
    }
}

handle1.addEventListener('mousedown', (e) => startResize(e, handle1));
handle2.addEventListener('mousedown', (e) => startResize(e, handle2));

// Mindmap selection
async function selectMindmap(element, graphId) {
    document.querySelectorAll('.mindmap-item').forEach(item => {
        item.classList.remove('active');
    });
    if (element) element.classList.add('active');
    
    currentGraphId = graphId;
    currentMindmapId = graphId;

    await switchMindmap(graphId);
    
    // Fetch graph data from API
    const graphData = await fetchGraphData(graphId);
    if (graphData) {
        currentGraphData = graphData;
        const rootBlock = graphData.nodes.find(n => n.id === graphData.root_block_id);
        if (rootBlock) {
            document.getElementById('mindmapTitle').textContent = rootBlock.label;
            currentBlockId = rootBlock.id;  // Set current block to root
            await switchBlock(rootBlock.id);
        }
        drawMindmap(graphData);
        
        // Load initial block messages
        if (graphData.root_block_id) {
            await loadBlockMessages(graphData.root_block_id);
        }
    }
}

// Draw mindmap using D3.js force-directed graph with API data
function drawMindmap(graphData) {
    const svg = d3.select('#mindmapSvg');
    svg.selectAll('*').remove(); // Clear previous graph
    
    const container = document.querySelector('#mindmapSvg').parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
        console.warn('No graph data to display');
        return;
    }
    
    // Create force simulation
    simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(50));
    
    // Create links with relation-based coloring
    const link = svg.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('stroke', d => d.color || '#999')
        .attr('stroke-width', d => d.strokeWidth || 2)
        .attr('stroke-opacity', 0.7)
        .attr('title', d => `${d.relation} (${(d.confidence * 100).toFixed(0)}%)`);
    
    // Create nodes
    const node = svg.append('g')
        .selectAll('g')
        .data(graphData.nodes)
        .enter().append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circles for nodes
    node.append('circle')
        .attr('r', d => d.id === graphData.root_block_id ? 30 : 20)
        .attr('fill', d => d.is_current ? '#FF6B6B' : (d.id === graphData.root_block_id ? '#0d6efd' : '#6610f2'))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', async (event, d) => {
            // Clicking a node just loads its messages into the chat panel.
            await switchBlock(d.id);
            await loadBlockMessages(d.id);
            
            // Update current block highlighting
            d3.selectAll('circle').attr('fill', node_d => 
                node_d.id === d.id ? '#FF6B6B' : (node_d.id === graphData.root_block_id ? '#0d6efd' : '#6610f2')
            );
            currentBlockId = d.id;
        });
    
    // Add labels
    node.append('text')
        .text(d => d.label)
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .attr('font-size', d => d.id === graphData.root_block_id ? '14px' : '12px')
        .attr('font-weight', d => d.id === graphData.root_block_id ? 'bold' : 'normal')
        .attr('fill', '#333')
        .style('pointer-events', 'none');
    
    // Update positions on simulation tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// Initialize mindmap on page load
window.addEventListener('load', async () => {
    // Load mindmaps from API
    const mindmaps = await fetchMindmaps();
    allMindmaps = mindmaps;
    
    // Populate mindmap list
    const mindmapList = document.querySelector('.mindmap-list');
    mindmapList.innerHTML = '';
    
    if (mindmaps.length === 0) {
        // Show empty state with instruction to create new mindmap
        document.getElementById('mindmapTitle').textContent = 'Graph';
        const svg = d3.select('#mindmapSvg');
        svg.selectAll('*').remove();
        svg.append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.3em')
            .attr('fill', '#999')
            .attr('font-size', '16px')
            .text('No mindmaps. Type "/new" to create one.');
        
        // Show placeholder in right panel
        const rightHeader = document.querySelector('.right-panel-header');
        rightHeader.innerHTML = '<h3>Ready to chat</h3>';
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '<div style="color: #999; text-align: center; margin-top: 20px;">Create a mindmap with /new to start</div>';
        return;
    }
    
    // Populate mindmap list
    mindmaps.forEach((mindmap, index) => {
        const li = document.createElement('li');
        li.className = 'mindmap-item' + (mindmap.is_current ? ' active' : '');
        li.innerHTML = `
            <span class="mindmap-title">${mindmap.title}</span>
            <button class="mindmap-delete-btn" onclick="deleteMindmap(event, '${mindmap.graph_id}')">x</button>
        `;
        li.onclick = function() { selectMindmap(this, mindmap.graph_id); };
        mindmapList.appendChild(li);
        
        if (index === 0 || mindmap.is_current) {
            selectMindmap(li, mindmap.graph_id);
        }
    });
});

// Load block messages and display in right panel
async function loadBlockMessages(blockId) {
    const blockData = await fetchBlockMessages(blockId);
    if (!blockData) return;
    
    currentBlockId = blockId;
    
    // Update right panel header
    const rightHeader = document.querySelector('.right-panel-header');
    rightHeader.innerHTML = `<h3>${blockData.title}</h3><p style="font-size: 12px; color: #666;">${blockData.intent || 'No intent'}</p>`;
    
    // Clear and populate messages
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
    
    blockData.messages.forEach(msg => {
        const wrapper = document.createElement('div');
        wrapper.className = `chat-message-wrapper ${msg.role}`;
        const timestamp = new Date(msg.timestamp * 1000).toLocaleTimeString();
        wrapper.innerHTML = `
            <div class="chat-message">
                <div class="chat-bubble">${msg.content}</div>
                <div class="chat-timestamp">${timestamp}</div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
    });
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Chat functionality
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    // Treat /new as a shortcut to "start a new conversation" via chat endpoint
    if (message === '/new') {
        input.value = '';
        autoResizeTextarea();
        return addMindmap();
    }

    const chatMessages = document.getElementById('chatMessages');

    // Optimistic user message
    const userWrapper = document.createElement('div');
    userWrapper.className = 'chat-message-wrapper user';
    userWrapper.innerHTML = `<div class="chat-message"><div class="chat-bubble">${message}</div><div class="chat-timestamp">Just now</div></div>`;
    chatMessages.appendChild(userWrapper);

    input.value = '';
    autoResizeTextarea();

    const result = await chatWithAssistant(message);
    if (!result) return;

    // Update current graph and block from response
    currentGraphId = result.graph_id;
    currentMindmapId = result.graph_id;
    currentBlockId = result.current_block_id;

    // Redraw mindmap from returned graph
    if (result.graph) {
        currentGraphData = result.graph;
        drawMindmap(result.graph);
    }

    // Replace chat panel with full message history for current block
    chatMessages.innerHTML = '';
    result.messages.forEach(msg => {
        const wrapper = document.createElement('div');
        wrapper.className = `chat-message-wrapper ${msg.role}`;
        const timestamp = new Date(msg.timestamp * 1000).toLocaleTimeString();
        wrapper.innerHTML = `
            <div class="chat-message">
                <div class="chat-bubble">${msg.content}</div>
                <div class="chat-timestamp">${timestamp}</div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Auto-resize textarea as user types
const messageInput = document.getElementById('messageInput');

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
}

messageInput.addEventListener('input', autoResizeTextarea);

// Allow Enter key to send (Ctrl+Enter for new line)
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.ctrlKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Add mindmap function - starts a new conversation via /api/chat
async function addMindmap() {
    const topic = prompt('What would you like to discuss?');
    if (!topic) return;  // User cancelled

    const result = await chatWithAssistant(topic);
    if (!result) return;

    // Update current graph and block
    currentGraphId = result.graph_id;
    currentMindmapId = result.graph_id;
    currentBlockId = result.current_block_id;

    // Refresh mindmap list from storage
    const mindmaps = await fetchMindmaps();
    allMindmaps = mindmaps;

    const mindmapList = document.querySelector('.mindmap-list');
    mindmapList.innerHTML = '';

    mindmaps.forEach((mindmap) => {
        const li = document.createElement('li');
        li.className = 'mindmap-item' + (mindmap.is_current ? ' active' : '');
        li.innerHTML = `
            <span class="mindmap-title">${mindmap.title}</span>
            <button class="mindmap-delete-btn" onclick="deleteMindmap(event, '${mindmap.graph_id}')">x</button>
        `;
        li.onclick = function() { selectMindmap(this, mindmap.graph_id); };
        mindmapList.appendChild(li);
    });

    // Select the new mindmap visually
    const firstItem = mindmapList.querySelector('.mindmap-item');
    if (firstItem) {
        await selectMindmap(firstItem, currentGraphId);
    }
}

// Delete mindmap function (not implemented)
function deleteMindmap(event, graphId) {
    event.stopPropagation();
    alert('Mindmap deletion is not yet implemented. Use the CLI to manage mindmaps.');
}
