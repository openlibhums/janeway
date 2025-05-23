let attentionTimeout = null;

const headerElements = ['h1, h2, h3, h4, h5, h6'];
const blockElements = ['p', 'li', 'ul', 'ol',' div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];

function drawUserAttention(link, targetElement){
 
    // Clear any existing timeout (allows a second link to be clicked before the timeout ends)
    if (attentionTimeout) {
        clearTimeout(attentionTimeout);
    }

    if(targetElement.matches(headerElements)  || targetElement.matches(blockElements)) {
        element = targetElement;
    }
    else{
        element = targetElement.closest(blockElements.join(','));
    }
    
    if (element) {

        element.classList.add('draw-attention');
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        //A11y for keyboard & screenreader
        oldTabIndex = targetElement.tabIndex;
        targetElement.tabIndex = "-1"
        targetElement.focus();
        
        attentionTimeout = setTimeout(() => {
            element.classList.remove('draw-attention');
            attentionTimeout = null;
            targetElement.tabIndex = oldTabIndex;
        }, 2000);
    }

}

// Function to get the section title for a reference
function getHeading(link) {
    let current = link;
    while (current) {
        // Check if current element is a heading
        if (current.matches(headerElements)) {
            // Ensure heading has an ID
            if (!current.id) {
                current.id = 'section-' + Math.random().toString(36).substring(2, 11);
            }
            return {
                title: current.textContent,
                id: current.id
            };
        }
        // Move to previous sibling or parent
        current = current.previousElementSibling || current.parentElement;
    }
    return { title: '', id: '' };
}

// Function to get or create ID for block container
function getBlockContainerId(element) {

    const container = element.closest(blockElements.join(','));
    
    if (container) {
        if (!container.id) {
            container.id = 'block-' + Math.random().toString(36).substring(2, 11);
        }
        return container.id;
    }
    return null;
}

// insert ids for all cross references, and backlinks for their destinations
function initialiseCrossRefs(){

    document.querySelectorAll('.cross-ref-entry').forEach(entry => {
        const links = Array.from(document.querySelectorAll(`.xref-bibr[href="#${entry.id}"]`));

        links.forEach((link, i) => {
            // ensure each in-text citation has a unique ID
            if (!link.id) {
                link.id = `cite-${entry.id}-${i+1}`;
            }

            const containerId = getBlockContainerId(link) || link.id;
            const heading = getHeading(link);

            const sectionLink = document.createElement('a');
            sectionLink.href = `#${containerId}`;
            sectionLink.textContent = links.length === 1 ? '---^' : `---^(${i + 1})`;
            sectionLink.setAttribute('aria-label', `${link.textContent}, ${heading.title}`);
            sectionLink.className = 'section-link';
            sectionLink.title = `${heading.title}`;

            sectionLink.dataset.citationId = link.id;
            
            entry.appendChild(sectionLink);
        });
    });
}


// Run initialiseCrossRefs when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    initialiseCrossRefs();
    
    // Add click handler for all internal links, including dynamically generated ones
    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href^="#"]');
        if (link) {
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                // Prevent default scroll behavior since we're handling it
                event.preventDefault();
                // Update the URL hash
                window.location.hash = targetId;
                // Draw attention to the target
                drawUserAttention(link, targetElement);
            }
        }
    });
});