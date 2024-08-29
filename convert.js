// npm install --save aglio
// npm install --save puppeteer
const fs = require('fs');
const aglio = require('aglio');
const puppeteer = require('puppeteer');
const path = require('path');

// Read the .apib file
const apibFile = path.join(__dirname, 'apiary.apib');

// fs.readFile(apibFile, 'utf8', (err, data) => {
//     if (err) {
//         console.error(`Error reading ${apibFile}:`, err);
//         return;
//     }

//     // Render the API Blueprint to HTML using Aglio
//     aglio.render(data, { themeVariables: 'default', themeCondenseNav: false }, (err, html, warnings) => {
//         if (err) {
//             console.error('Error rendering HTML:', err);
//             return;
//         }

//         // Output the HTML to a file
//         const outputFile = 'output.html';
//         fs.writeFile(outputFile, html, (err) => {
//             if (err) {
//                 console.error(`Error writing ${outputFile}:`, err);
//                 return;
//             }
//             console.log(`HTML output written to ${outputFile}`);
//             convertHtmlToPdf();
//         });

//         // Print any warnings
//         if (warnings) {
//             console.warn('Warnings:', warnings);
//         }
//     });
// });

async function convertHtmlToPdf() {
    // Launch a new browser instance
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Load the HTML file
    const htmlPath = path.join(__dirname, 'output.html');
    await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });

    // Define the PDF path
    const pdfPath = path.join(__dirname, 'output.pdf');

    // Set the page dimensions to fit content
    await page.evaluate(() => {
        document.body.style.width = '100%';
        document.body.style.margin = '0';
        document.body.style.padding = '0';
    });

    // Generate the PDF
    await page.pdf({
        path: pdfPath,
        format: 'A4',
        printBackground: true
    });

    // Close the browser
    await browser.close();

    console.log(`PDF generated at ${pdfPath}`);
}
convertHtmlToPdf();
