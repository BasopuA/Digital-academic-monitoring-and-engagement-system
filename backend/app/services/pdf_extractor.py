import os
from typing import Optional
from PyPDF2 import PdfReader
from io import BytesIO


class PDFExtractor:
    """Extract text content from PDF files"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Optional[str]:
        """Extract text from a PDF file"""
        try:
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip() if text else None
            
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes) -> Optional[str]:
        """Extract text from PDF bytes"""
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            text = ""
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip() if text else None
            
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF bytes: {str(e)}")