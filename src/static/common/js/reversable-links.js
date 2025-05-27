let attentionTimeout = null;

const headerElements = ['h1, h2, h3, h4, h5, h6'];
const blockElements = ['p', 'li', 'ul', 'ol',' div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];



function drawUserAttention(targetElement){
 
    // Clear any existing timeout (allows a second link to be clicked before the timeout ends)
    if (attentionTimeout) {
        clearTimeout(attentionTimeout);
    }

    // if the target is not a heading or a block, uses closest block
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
        const viewportHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;

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

        element.classList.add('draw-attention');
        scrollToElementWithOffset(targetElement, 100);
        
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

    document.querySelectorAll('.cross-ref-entry').forEach(entry => {
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
            sectionLink.setAttribute('aria-label', `${link.textContent}, ${heading.title}`);
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