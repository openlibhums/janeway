// draw user attention to destination
function drawUserAttention(link, targetElement){
    console.log('Drawing attention to:', targetElement);
    
    // visual highlighting around the closest block-level container
    const blockElements = ['p', 'li', 'div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];
    const element = targetElement.closest(blockElements.join(','));
    console.log('Found container element:', element);
    
    if (element) {
        console.log('Adding draw-attention class');
        element.classList.add('draw-attention');

        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        setTimeout(() => {
            console.log('Removing draw-attention class');
            element.classList.remove('draw-attention');
        }, 2000);
    }

    //keyboard A11y - only focus if element is focusable
    if (targetElement.tagName === 'A' || targetElement.tagName === 'BUTTON' || 
        targetElement.getAttribute('tabindex') !== null) {
        targetElement.focus();
    }

    //screen reader A11y (user dismissable sr-only announcement)
    const term = link.textContent;
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('class', 'sr-only dismissible-announcement');
    announcement.textContent = `Navigated to reference: ${term}`;

    const dismissButton = document.createElement('button');
    dismissButton.setAttribute('aria-label', 'Dismiss announcement');
    dismissButton.setAttribute('class', 'dismiss-announcement');
    dismissButton.innerHTML = '&times;';
    dismissButton.addEventListener('click', () => announcement.remove());
    
    announcement.appendChild(dismissButton);
    document.body.appendChild(announcement);
}

// from article to cross reference on the same page 
// function navigateToReference(targetId, sourceLink){
//     // first remember where you came from!
//     lastArticlePosition = sourceLink;

//     // then scroll
//     link.scrollIntoView({ behavior: 'smooth'});

//     // and after scrolling ...
//     setTimeout(() => {

//         //@todo update target 'return' button to last article position

//         drawUserAttention(targetId)

//     }, 500);
// }

// Navigate from a cross reference dropdown back to the article
// function backToArticle(link) {
//     if(lastArticlePosition){
//         const articlePosition = lastArticlePosition
    
//         // move
//         articlePosition.scrollIntoView({ behaviour: 'smooth'});

//         // and while moving
//         setTimeout(() => {
//             //@todo reset target 'return' button to first link from article

//             drawUserAttention(articlePosition);
//         }, 500);
//     }   
// }

// Handle cross-reference link clicks
// document.querySelectorAll('.cross-ref-link').forEach(link => {
//     link.addEventListener('click', function(e){
//         e.preventDefault();
//         const targetId = this.getAttribute('href').substring(1);
//         navigateToReference(targetId, this);
//     });
// });

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
            sectionLink.setAttribute('aria-labelledby', `${entry.id} ${sectionInfo.id}`);
            sectionLink.className = 'section-link';
            sectionLink.title = `${sectionInfo.title}`;
            sectionLink.tabIndex = 0; // Make sure the link is focusable
            
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