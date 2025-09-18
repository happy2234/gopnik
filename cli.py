import argparse
import os
from ocr import process_image_ocr
from pii_detection import detect_pii
from redaction_engine import redact_pii
from logger import setup_logger, log_processing
from config import SUPPORTED_EXTENSIONS, DEFAULT_OUTPUT_DIR

def process_file(input_path, output_dir):
    """Process a single file through the OCR and redaction pipeline"""
    logger = setup_logger()
    
    try:
        # Perform OCR
        ocr_results = process_image_ocr(input_path)
        
        # Detect PII
        pii_results = detect_pii(ocr_results)
        
        # Redact PII
        output_path = redact_pii(input_path, pii_results, output_dir)
        
        # Log processing
        log_processing(input_path, output_path, pii_results, logger)
        
        return output_path, pii_results
        
    except Exception as e:
        logger.error(f"Error processing {input_path}: {str(e)}")
        raise

def process_directory(input_dir, output_dir):
    """Process all supported files in a directory"""
    processed_files = []
    
    for filename in os.listdir(input_dir):
        if any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            input_path = os.path.join(input_dir, filename)
            output_path, pii_results = process_file(input_path, output_dir)
            processed_files.append((input_path, output_path, len(pii_results)))
    
    return processed_files

def main():
    parser = argparse.ArgumentParser(description="Gopnik AI Toolkit - CLI Mode")
    parser.add_argument("--input", "-i", required=True, help="Input file or directory")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Process based on input type
    if os.path.isfile(args.input):
        output_path, pii_results = process_file(args.input, args.output)
        print(f"Processed: {args.input} -> {output_path}")
        print(f"Found {len(pii_results)} PII instances")
        
    elif os.path.isdir(args.input):
        processed_files = process_directory(args.input, args.output)
        print(f"Processed {len(processed_files)} files:")
        for input_path, output_path, pii_count in processed_files:
            print(f"  {input_path} -> {output_path} ({pii_count} PII instances)")
    
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())