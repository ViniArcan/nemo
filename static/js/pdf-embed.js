import * as pdfjsLib from '../pdfjs/build/pdf.mjs';

document.addEventListener("DOMContentLoaded", function() {
    // Set the path to the worker script
    pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/pdfjs/build/pdf.worker.mjs';

    // Find all links with the class 'pdf-embed'
    const pdfLinks = document.querySelectorAll('a.pdf-embed');

    pdfLinks.forEach(link => {
        const url = link.href;
        
        // Create a container for our viewer
        const viewerContainer = document.createElement('div');
        viewerContainer.classList.add('pdf-viewer-container');
        
        // Create the download button
        const downloadBtn = document.createElement('a');
        downloadBtn.href = url;
        downloadBtn.textContent = 'Fazer Download do PDF';
        downloadBtn.classList.add('pdf-download-btn');
        downloadBtn.setAttribute('download', url.split('/').pop());
        
        // Add the button to our container (it will be at the end)
        viewerContainer.appendChild(downloadBtn);
        
        // Replace the original link with our new viewer container
        link.parentNode.replaceChild(viewerContainer, link);

        // --- NEW: Asynchronous function to render all pages ---
        const renderAllPages = async (pdf) => {
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                const page = await pdf.getPage(pageNum);
                
                const scale = 1.5;
                const viewport = page.getViewport({ scale: scale });

                // Create a canvas for this specific page
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                // Insert the canvas before the download button
                viewerContainer.insertBefore(canvas, downloadBtn);

                // Render PDF page into canvas context
                const renderContext = {
                    canvasContext: context,
                    viewport: viewport
                };
                await page.render(renderContext).promise;
                console.log(`Page ${pageNum} rendered`);
            }
        };

        // --- Initialize PDF.js ---
        const loadingTask = pdfjsLib.getDocument(url);
        loadingTask.promise.then(function(pdf) {
            console.log('PDF loaded');
            renderAllPages(pdf); // Call our new function to render every page
        }, function (reason) {
            console.error(reason);
            viewerContainer.textContent = "Error: Could not load PDF.";
        });
    });
});