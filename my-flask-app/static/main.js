let leftWidth = 20;
let middleWidth = 40;
let isResizing = false;
let currentHandle = null;

// Resizable panels
const handle1 = document.getElementById('handle1');
const handle2 = document.getElementById('handle2');
const contentWrapper = document.querySelector('.content-wrapper');

// Dummy mindmap data structures (simulating conversation graph)
const mindmapData = {
    1: { // Machine Learning
        nodes: [
            { id: 'ml-root', label: 'Machine Learning', type: 'root' },
            { id: 'ml-supervised', label: 'Supervised Learning', type: 'child' },
            { id: 'ml-unsupervised', label: 'Unsupervised Learning', type: 'child' },
            { id: 'ml-regression', label: 'Regression', type: 'grandchild' },
            { id: 'ml-classification', label: 'Classification', type: 'grandchild' },
            { id: 'ml-clustering', label: 'Clustering', type: 'grandchild' }
        ],
        links: [
            { source: 'ml-root', target: 'ml-supervised' },
            { source: 'ml-root', target: 'ml-unsupervised' },
            { source: 'ml-supervised', target: 'ml-regression' },
            { source: 'ml-supervised', target: 'ml-classification' },
            { source: 'ml-unsupervised', target: 'ml-clustering' }
        ]
    },
    2: { // Web Development
        nodes: [
            { id: 'web-root', label: 'Web Development', type: 'root' },
            { id: 'web-frontend', label: 'Frontend', type: 'child' },
            { id: 'web-backend', label: 'Backend', type: 'child' },
            { id: 'web-react', label: 'React', type: 'grandchild' },
            { id: 'web-vue', label: 'Vue.js', type: 'grandchild' },
            { id: 'web-flask', label: 'Flask', type: 'grandchild' }
        ],
        links: [
            { source: 'web-root', target: 'web-frontend' },
            { source: 'web-root', target: 'web-backend' },
            { source: 'web-frontend', target: 'web-react' },
            { source: 'web-frontend', target: 'web-vue' },
            { source: 'web-backend', target: 'web-flask' }
        ]
    },
    3: { // Python Tips
        nodes: [
            { id: 'py-root', label: 'Python Tips', type: 'root' },
            { id: 'py-syntax', label: 'Syntax', type: 'child' },
            { id: 'py-libs', label: 'Libraries', type: 'child' },
            { id: 'py-comprehensions', label: 'List Comprehensions', type: 'grandchild' }
        ],
        links: [
            { source: 'py-root', target: 'py-syntax' },
            { source: 'py-root', target: 'py-libs' },
            { source: 'py-syntax', target: 'py-comprehensions' }
        ]
    },
    4: { // AI Ethics
        nodes: [
            { id: 'ethics-root', label: 'AI Ethics', type: 'root' },
            { id: 'ethics-bias', label: 'Bias & Fairness', type: 'child' },
            { id: 'ethics-privacy', label: 'Privacy', type: 'child' }
        ],
        links: [
            { source: 'ethics-root', target: 'ethics-bias' },
            { source: 'ethics-root', target: 'ethics-privacy' }
        ]
    },
    5: { // Cloud Computing
        nodes: [
            { id: 'cloud-root', label: 'Cloud Computing', type: 'root' },
            { id: 'cloud-aws', label: 'AWS', type: 'child' },
            { id: 'cloud-azure', label: 'Azure', type: 'child' },
            { id: 'cloud-gcp', label: 'GCP', type: 'child' }
        ],
        links: [
            { source: 'cloud-root', target: 'cloud-aws' },
            { source: 'cloud-root', target: 'cloud-azure' },
            { source: 'cloud-root', target: 'cloud-gcp' }
        ]
    }
};

let currentMindmapId = 1;
let simulation = null;

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
function selectMindmap(element, title, id) {
    document.querySelectorAll('.mindmap-item').forEach(item => {
        item.classList.remove('active');
    });
    element.classList.add('active');
    document.getElementById('mindmapTitle').textContent = title;
    currentMindmapId = id;
    drawMindmap(id);
}

// Draw mindmap using D3.js force-directed graph
function drawMindmap(mindmapId) {
    const svg = d3.select('#mindmapSvg');
    svg.selectAll('*').remove(); // Clear previous graph
    
    const container = document.querySelector('#mindmapSvg').parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const data = mindmapData[mindmapId];
    if (!data) return;
    
    // Create force simulation
    simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(50));
    
    // Create links
    const link = svg.append('g')
        .selectAll('line')
        .data(data.links)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.6);
    
    // Create nodes
    const node = svg.append('g')
        .selectAll('g')
        .data(data.nodes)
        .enter().append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circles for nodes
    node.append('circle')
        .attr('r', d => d.type === 'root' ? 30 : d.type === 'child' ? 20 : 15)
        .attr('fill', d => {
            if (d.type === 'root') return '#0d6efd';
            if (d.type === 'child') return '#6610f2';
            return '#6c757d';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    
    // Add labels
    node.append('text')
        .text(d => d.label)
        .attr('text-anchor', 'middle')
        .attr('dy', d => d.type === 'root' ? 45 : d.type === 'child' ? 35 : 30)
        .attr('font-size', d => d.type === 'root' ? '14px' : '12px')
        .attr('font-weight', d => d.type === 'root' ? 'bold' : 'normal')
        .attr('fill', '#333');
    
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
window.addEventListener('load', () => {
    drawMindmap(currentMindmapId);
});

// Chat functionality
function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    const chatMessages = document.getElementById('chatMessages');

    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-message user';
    const userInnerWrapper = document.createElement('div');
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble';
    userBubble.textContent = message;
    const userTimestamp = document.createElement('div');
    userTimestamp.className = 'chat-timestamp';
    userTimestamp.textContent = 'Just now';
    userInnerWrapper.appendChild(userBubble);
    userInnerWrapper.appendChild(userTimestamp);
    userDiv.appendChild(userInnerWrapper);
    chatMessages.appendChild(userDiv);

    input.value = '';

    // Simulate bot response
    setTimeout(() => {
        const botDiv = document.createElement('div');
        botDiv.className = 'chat-message bot';
        botDiv.innerHTML = `<div><div class="chat-bubble">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</div><div class="chat-timestamp">Just now</div></div>`;
        chatMessages.appendChild(botDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 500);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Allow Enter key to send
document.getElementById('messageInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
