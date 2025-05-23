// draw user attention to destination
let attentionTimeout = null;

function drawUserAttention(link, targetElement){
    console.log('Drawing attention to:', targetElement);
    
    // Clear any existing timeout
    if (attentionTimeout) {
        clearTimeout(attentionTimeout);
    }
    

    
    const blockElements = ['p', 'li', 'div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];
    const element = targetElement.closest(blockElements.join(','));
    
    if (element) {

        // visual highlighting around the closest block-level container
        element.classList.add('draw-attention');

        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        //keyboard A11y - make the focus change to this element
        oldTabIndex = targetElement.tabIndex;
        targetElement.tabIndex = "-1"
        targetElement.focus();
        
        attentionTimeout = setTimeout(() => {
            element.classList.remove('draw-attention');
            attentionTimeout = null;
            targetElement.tabIndex - oldTabIndex;
        }, 2000);
    }

}

// Function to get the section title for a reference
function getSectionTitle(link) {
    let current = link;
    while (current) {
        // Check if current element is a heading
        if (current.matches('h1, h2, h3, h4, h5, h6')) {
            // Ensure heading has an ID
            if (!current.id) {
                current.id = 'section-' + Math.random().toString(36).substr(2, 9);
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

// insert ids for all cross references, and backlinks for their destinations
function initialiseCrossRefs(){

    document.querySelectorAll('.cross-ref-entry').forEach(entry => {
        const links = Array.from(document.querySelectorAll(`.xref-bibr[href="#${entry.id}"]`));

        links.forEach((link, i) => {
            // Assign a unique id to each in-text citation if it doesn't have one
            if (!link.id) {
                link.id = `cite-${entry.id}-${i+1}`;
            }
            const sectionInfo = getSectionTitle(link);
            
            // Create a new link element
            const sectionLink = document.createElement('a');
            sectionLink.href = `#${link.id}`; // Link to the original citation's position
            sectionLink.textContent = links.length === 1 ? '---^' : `---^(${i + 1})`;
            sectionLink.setAttribute('aria-label', `${sectionInfo.title}`);
            sectionLink.className = 'section-link';
            sectionLink.title = `${sectionInfo.title}`;
            
            // Append the link as a suffix within the entry
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