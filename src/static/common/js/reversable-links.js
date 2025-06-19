let attentionTimeouts = new Map(); // Track timeouts per element

const headerElements = ['h1, h2, h3, h4, h5, h6'];
const blockElements = ['p', 'li', 'ul', 'ol',' div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];



function drawUserAttention(targetElement){
 
    // if the target is not a heading or a block, uses closest block
    let element;
    if(targetElement.matches(headerElements)  || targetElement.matches(blockElements)) {
        element = targetElement;
    }
    else{
        element = targetElement.closest(blockElements.join(','));
    }

    // Function to smoothly scroll to element with offset if needed
    function scrollToElementWithOffset(element, offset) {
        const rect = element.getBoundingClientRect();
        const elementTop = window.pageYOffset + rect.top;

        // Only apply offset if element would scroll to top
        let finalPosition = elementTop;
        if (Math.max(0, elementTop) === elementTop) { 
            finalPosition -= offset;
        }
        
        window.scrollTo({
            top: finalPosition,
            behavior: 'smooth'
        });
    }

    if (element) {
        // Clear any existing timeout for this element
        if (attentionTimeouts.has(element)) {
            clearTimeout(attentionTimeouts.get(element));
        }
        
        scrollToElementWithOffset(element, 100);
        element.classList.add('draw-attention');
        
        //A11y for keyboard & screenreader
        const oldTabIndex = element.hasAttribute('tabIndex') ? element.tabIndex : null;
        element.tabIndex = "-1"
        element.focus();
        
        const timeout = setTimeout(() => {
            element.classList.remove('draw-attention');
            if (element.classList.length === 0) {
                element.removeAttribute('class');
            }
            if (oldTabIndex === null) {
                element.removeAttribute('tabIndex');
            } else {
                element.tabIndex = oldTabIndex;
            }
            attentionTimeouts.delete(element);
        }, 2000);
        
        attentionTimeouts.set(element, timeout);
    }

}

// Function to get the article section heading linked from
function getHeading(link) {
    let current = link;
    while (current) {
        if (current.matches(headerElements)) {
            if (!current.id) {
                current.id = 'section-' + Math.random().toString(36).substring(2, 11);
            }
            return {
                title: current.textContent,
                id: current.id
            };
        }
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

    document.querySelectorAll('#reflist li').forEach(entry => {
        const links = Array.from(document.querySelectorAll(`.xref-bibr[href="#${entry.id}"]`));

        links.forEach((link, i) => {
            if (!link.id) {
                link.id = `cite-${entry.id}-${i+1}`;
            }

            const containerId = getBlockContainerId(link) || link.id;
            const heading = getHeading(link);

            const sectionLink = document.createElement('a');
            sectionLink.href = `#${containerId}`;
            sectionLink.textContent = links.length === 1 ? '---^' : `---^(${i + 1})`;
            const prefix = links.length === 1 ? "" : `${i + 1} of ${links.length}, `
            sectionLink.setAttribute('aria-label', `in text ${prefix}: ${heading.title}, ${link.textContent}`);
            sectionLink.className = 'section-link';
            sectionLink.title = `${heading.title}`;

            sectionLink.dataset.citationId = link.id;
            
            entry.appendChild(sectionLink);
        });
    });
}


document.addEventListener('DOMContentLoaded', () => {
    initialiseCrossRefs();
    
    // Add click handler for *all* internal links
    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href^="#"]');
        if (link) {
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                event.preventDefault();
                window.location.hash = targetId;
                drawUserAttention(targetElement);
            }
        }
    });
});