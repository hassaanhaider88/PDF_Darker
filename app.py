import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageOps
import io

app = Flask(__name__)


def invert_except_images(page, pix):
    """Invert page except image regions."""
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

    # Create mask (white where image exists, black elsewhere)
    mask = Image.new("L", img.size, 0)

    for img_info in page.get_images(full=True):
        xref = img_info[0]

        # Extract image boundary
        rects = page.get_image_rects(xref)
        for r in rects:
            # Convert PDF coordinates to pixel coordinates
            x0 = int(r.x0 * pix.xres / 72)
            y0 = int(r.y0 * pix.yres / 72)
            x1 = int(r.x1 * pix.xres / 72)
            y1 = int(r.y1 * pix.yres / 72)

            # Mark area as "image area" (white)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    mask.putpixel((x, y), 255)

    # Invert whole page
    inverted = ImageOps.invert(img)

    # Composite:
    # - Where mask is white → original image
    # - Where mask is black → inverted text/background
    final = Image.composite(img, inverted, mask)

    return final


def process_pdf_in_memory(input_pdf_bytes):
    input_pdf = fitz.open(stream=input_pdf_bytes, filetype="pdf")
    output_pdf = fitz.open()

    for page_num in range(len(input_pdf)):
        page = input_pdf[page_num]
        image_list = page.get_images(full=True)

        # Render page as high-res image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        if image_list:
            # Invert only background + text
            final_img = invert_except_images(page, pix)
        else:
            # Fully invert normal pages
            final_img = ImageOps.invert(
                Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            )

        # Convert final image to bytes
        buf = io.BytesIO()
        final_img.save(buf, format="JPEG", quality=95)
        img_bytes = buf.getvalue()

        # Create new PDF page
        new_page = output_pdf.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, stream=img_bytes)

    # Return output PDF bytes
    out_buffer = io.BytesIO()
    output_pdf.save(out_buffer)
    out_buffer.seek(0)

    input_pdf.close()
    output_pdf.close()

    return out_buffer


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/view-pdf')
def viewpdf():
    return render_template('ViewPDF.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400

    if not file.filename.lower().endswith('.pdf'):
        return 'Invalid file type', 400

    try:
        input_bytes = file.read()
        output_pdf_buffer = process_pdf_in_memory(input_bytes)

        return send_file(
            output_pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"dark_{file.filename}"
        )

    except Exception as e:
        return f"Error: {e}", 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)


# import os
# import fitz  # pymupdf
# from flask import Flask, render_template, request, send_file, after_this_request
# from PIL import Image, ImageOps
# import io

# app = Flask(__name__)
# UPLOAD_FOLDER = 'uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# def invert_image_colors(image_bytes):
#     """Inverts the colors of an image (bytes) and returns bytes."""
#     img = Image.open(io.BytesIO(image_bytes))
#     # Convert to RGB if not already (to handle transparent PNGs etc if needed, though usually PDF render is opaque)
#     if img.mode == 'RGBA':
#         img = img.convert('RGB')
    
#     inverted_img = ImageOps.invert(img)
    
#     output_buffer = io.BytesIO()
#     inverted_img.save(output_buffer, format='JPEG', quality=95)
#     return output_buffer.getvalue()

# def process_pdf(input_path, output_path):
#     doc = fitz.open(input_path)
#     out_doc = fitz.open()

#     for page_num in range(len(doc)):
#         page = doc[page_num]
#         image_list = page.get_images()

#         if image_list:
#             # Page has images, keep original
#             out_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
#         else:
#             # Text only page, render and invert
#             # Render page to image (high resolution)
#             pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
#             img_data = pix.tobytes("png")
            
#             # Invert colors
#             inverted_img_data = invert_image_colors(img_data)
            
#             # Create a new page in output doc with same dimensions
#             new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
            
#             # Insert the inverted image to cover the whole page
#             new_page.insert_image(page.rect, stream=inverted_img_data)

#     out_doc.save(output_path)
#     doc.close()
#     out_doc.close()

# @app.route('/', methods=['GET'])
# def index():
#     return render_template('index.html')

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return 'No file part', 400
#     file = request.files['file']
#     if file.filename == '':
#         return 'No selected file', 400
    
#     if file and file.filename.lower().endswith('.pdf'):
#         input_path = os.path.join(UPLOAD_FOLDER, file.filename)
#         output_filename = f"dark_{file.filename}"
#         output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
#         file.save(input_path)
        
#         try:
#             process_pdf(input_path, output_path)
            
#             # Clean up input file immediately
#             if os.path.exists(input_path):
#                 os.remove(input_path)

#             @after_this_request
#             def remove_file(response):
#                 try:
#                     if os.path.exists(output_path):
#                         os.remove(output_path)
#                 except Exception as e:
#                     app.logger.error(f"Error removing file: {e}")
#                 return response

#             return send_file(output_path, as_attachment=True)
            
#         except Exception as e:
#             return f"An error occurred: {str(e)}", 500
            
#     return 'Invalid file type', 400

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
