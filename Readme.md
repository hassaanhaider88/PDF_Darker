# PDF Dark Mode Converter

A powerful, local web application that automatically converts your PDF documents into a "Dark Mode" format. It intelligently inverts the colors of text-heavy pages (black background, white text) to reduce eye strain, while preserving the original quality of pages containing images, diagrams, or photos.

## 🌟 Features

*   **Smart Content Detection**: Automatically analyzes each page to determine if it contains images or just text.
*   **Intelligent Conversion**:
    *   **Text Pages**: Converted to high-contrast Dark Mode (Black Background / White Text).
    *   **Image Pages**: Left completely untouched to preserve the integrity of charts, diagrams, and photos.
*   **Privacy Focused**: Runs entirely on your local machine. No files are uploaded to the cloud.
*   **Modern UI**: A clean, dark-themed web interface for easy drag-and-drop uploads.
*   **Instant Download**: processed files are ready for download immediately after conversion.

## 🛠️ Technology Stack

*   **Python 3**: Core programming language.
*   **Flask**: Lightweight web framework for the application interface.
*   **PyMuPDF (fitz)**: High-performance PDF processing library.
*   **Pillow (PIL)**: Python Imaging Library for image manipulation and color inversion.
*   **HTML5/CSS3**: Responsive front-end design.

## 📋 Prerequisites

Before you begin, ensure you have **Python 3.6+** installed on your system.

## 🚀 Installation & Setup

1.  **Navigate to the project directory**:
    ```bash
    cd c:/Desktop/Pythons/pdfs
    ```

2.  **Install dependencies**:
    We use a `requirements.txt` file to manage dependencies. Run the following command:
    ```bash
    pip install -r requirements.txt
    ```
    *This will install `flask`, `pymupdf`, and `Pillow`.*

## 💻 How to Use

1.  **Start the Application**:
    Run the following command in your terminal:
    ```bash
    python app.py
    ```

2.  **Access the Interface**:
    Open your web browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

3.  **Convert a PDF**:
    *   Click the **"Click to select PDF"** area or drag and drop a `.pdf` file.
    *   Click the **"Convert & Download"** button.
    *   Wait for the process to finish. The converted file (`dark_filename.pdf`) will download automatically.

## ⚙️ How It Works (Technical Details)

The application processes the PDF page by page using the following logic:

1.  **Image Detection**: For every page, it checks `page.get_images()`.
2.  **Decision Making**:
    *   **If images are found**: The page is assumed to contain important visual data (charts, photos). The original page is copied directly to the output PDF to avoid ruining the images (e.g., inverting a photo looks bad).
    *   **If no images are found (Text Only)**:
        1.  The page is rendered into a high-resolution image (Rasterization).
        2.  The colors of this image are mathematically inverted (White -> Black, Black -> White).
        3.  This new "Dark Mode" image is inserted as a new page in the output PDF.

> **Note**: Converted text pages become images. This means you cannot select/highlight text on the dark pages in the output file. This is a necessary trade-off to ensure perfect visual inversion without breaking complex PDF layouts.

## 📂 Project Structure

```
pdfs/
├── app.py                # Main Flask application logic
├── requirements.txt      # List of Python dependencies
├── verify_logic.py       # Script for testing PDF conversion logic
├── templates/
│   └── index.html        # Front-end HTML interface
└── uploads/              # Temporary folder for processing files
```

## 🔧 Troubleshooting

*   **"ModuleNotFoundError"**: Make sure you ran `pip install -r requirements.txt`.
*   **Permission Errors**: Ensure you have write permissions in the folder where you are running the script.
*   **Port in Use**: If port 5000 is busy, the app might fail to start. You can change the port in `app.py` at the bottom (`app.run(port=5001)`).

---


Star this repo please 