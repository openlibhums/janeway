let attentionTimeouts = new Map(); // Track timeouts per element

const headerElements = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
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
        const elementTop = window.scrollY + rect.top;

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

        // Always create an ordered list, even for single items
        const ol = document.createElement('ol');
        ol.className = 'back-links-list';
        
        if (links.length === 1) {
            // Single link behavior
            const link = links[0];
            if (!link.id) {
                link.id = `cite-${entry.id}-1`;
            }

            const containerId = getBlockContainerId(link) || link.id;
            const heading = getHeading(link);

            const sectionLink = document.createElement('a');
            sectionLink.href = `#${containerId}`;
            sectionLink.textContent = '---^';
            sectionLink.setAttribute('aria-label', `${heading.title}, ${link.textContent}`);
            sectionLink.className = 'section-link';
            sectionLink.title = `${heading.title}`;
            sectionLink.dataset.citationId = link.id;
            
            const li = document.createElement('li');
            li.appendChild(sectionLink);
            ol.appendChild(li);
        } else {
            // Multiple links behavior - create ordered list with numbered aria-labels
            const headingCounts = new Map(); // Track count of each heading title
            
            // First pass: count occurrences of each heading title
            links.forEach(link => {
                const heading = getHeading(link);
                const title = heading.title;
                headingCounts.set(title, (headingCounts.get(title) || 0) + 1);
            });
            
            // Second pass: create links with appropriate numbering
            const headingNumbers = new Map(); // Track current number for each heading
            
            links.forEach((link, i) => {
                if (!link.id) {
                    link.id = `cite-${entry.id}-${i+1}`;
                }

                const containerId = getBlockContainerId(link) || link.id;
                const heading = getHeading(link);
                const title = heading.title;

                const sectionLink = document.createElement('a');
                sectionLink.href = `#${containerId}`;
                sectionLink.textContent = `---^(${i + 1})`;
                sectionLink.className = 'section-link';
                sectionLink.title = `${heading.title}`;
                sectionLink.dataset.citationId = link.id;
                
                // Generate aria-label with numbering for duplicate headings
                let ariaLabel = title;
                if (headingCounts.get(title) > 1) {
                    headingNumbers.set(title, (headingNumbers.get(title) || 0) + 1);
                    ariaLabel = `${ariaLabel} ${headingNumbers.get(title)}, ${link.textContent}`;
                }
                sectionLink.setAttribute('aria-label', ariaLabel);
                
                const li = document.createElement('li');
                li.appendChild(sectionLink);
                ol.appendChild(li);
            });
        }
        
        entry.appendChild(ol);
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