
def offline_interface():
    """Streamlit interface for offline processing"""
    st.title("Offline GUI Mode")
    st.info("Process documents locally on your machine. No data is sent to external servers.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a document for PII redaction", 
        type=SUPPORTED_EXTENSIONS,
        help="Supported formats: " + ", ".join(SUPPORTED_EXTENSIONS)
    )
    
    if uploaded_file is not None:
        # Check file size
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"File size exceeds maximum allowed size of {MAX_FILE_SIZE//1024//1024}MB")
            return
        
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size} bytes",
            "File type": uploaded_file.type
        }
        st.write(file_details)
        
        # Process file
        if st.button("Process and Redact PII"):
            with st.spinner("Processing document..."):
                try:
                    # Save uploaded file to temporary location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        input_path = tmp_file.name
                    
                    # Perform OCR
                    ocr_results = process_image_ocr(input_path)
                    
                    if not ocr_results:
                        st.warning("No text could be extracted from this document.")
                        return
                    
                    # Detect PII
                    pii_results = detect_pii(ocr_results)
                    
                    if not pii_results:
                        st.success("No PII detected in this document.")
                        os.unlink(input_path)
                        return
                    
                    # Create output directory
                    output_dir = tempfile.mkdtemp()
                    
                    # Redact PII
                    output_path = redact_pii(input_path, pii_results, output_dir)
                    
                    # Set up logger and log processing
                    logger = setup_logger()
                    log_processing(input_path, output_path, pii_results, logger)
                    
                    # Display results
                    st.success(f"Processing complete! Found {len(pii_results)} PII instances.")
                    
                    # Show PII details
                    with st.expander("View detected PII details"):
                        for i, pii in enumerate(pii_results):
                            st.write(f"{i+1}. {pii['type']}: {pii['text']} (confidence: {pii['confidence']:.2f})")
                    
                    # Download button for redacted file
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label="Download redacted document",
                            data=file,
                            file_name=f"redacted_{uploaded_file.name}",
                            mime=uploaded_file.type
                        )
                    
                    # Clean up temporary files
                    os.unlink(input_path)
                    # Note: output directory cleanup might be handled by system
                    
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    # Clean up on error
                    if 'input_path' in locals() and os.path.exists(input_path):
                        os.unlink(input_path)

if __name__ == "__main__":
    offline_interface()