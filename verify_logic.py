import fitz
from PIL import Image, ImageDraw
import os
from app import process_pdf

def create_test_pdf(filename):
    doc = fitz.open()
    
    # Page 1: Text only (Should be inverted)
    page1 = doc.new_page()
    page1.insert_text((50, 50), "This is page 1. Text only. Should be inverted.", fontsize=20)
    
    # Page 2: Text + Image (Should NOT be inverted)
    page2 = doc.new_page()
    page2.insert_text((50, 50), "This is page 2. Text + Image. Should NOT be inverted.", fontsize=20)
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save('temp_img.png')
    page2.insert_image(fitz.Rect(100, 100, 200, 200), filename='temp_img.png')
    
    # Page 3: Text only (Should be inverted)
    page3 = doc.new_page()
    page3.insert_text((50, 50), "This is page 3. Text only. Should be inverted.", fontsize=20)
    
    doc.save(filename)
    doc.close()
    if os.path.exists('temp_img.png'):
        os.remove('temp_img.png')

def verify_pdf(filename):
    doc = fitz.open(filename)
    
    # Check Page 1
    # It should be an image now (since we rasterize and invert)
    # Or at least, it should have an image covering the page.
    page1 = doc[0]
    images1 = page1.get_images()
    print(f"Page 1 images: {len(images1)}")
    if len(images1) == 0:
        print("FAIL: Page 1 should have been rasterized to an image.")
    else:
        print("PASS: Page 1 has an image (rasterized).")

    # Check Page 2
    # Should be original structure (text + image)
    # But wait, the original page had an image.
    # If we kept the original page, it should still have that 1 image.
    page2 = doc[1]
    images2 = page2.get_images()
    print(f"Page 2 images: {len(images2)}")
    if len(images2) >= 1:
         print("PASS: Page 2 preserved images.")
    else:
         print("FAIL: Page 2 lost images.")

    # Check Page 3
    page3 = doc[2]
    images3 = page3.get_images()
    print(f"Page 3 images: {len(images3)}")
    if len(images3) > 0:
        print("PASS: Page 3 has an image (rasterized).")
    else:
        print("FAIL: Page 3 should have been rasterized.")

    doc.close()

if __name__ == "__main__":
    input_pdf = "test_input.pdf"
    output_pdf = "test_output.pdf"
    
    print("Creating test PDF...")
    create_test_pdf(input_pdf)
    
    print("Processing PDF...")
    process_pdf(input_pdf, output_pdf)
    
    print("Verifying output...")
    verify_pdf(output_pdf)
    
    # Cleanup
    # os.remove(input_pdf)
    # os.remove(output_pdf)
