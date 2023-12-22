def generate_large_html(file_name, target_size_mb):
    sample_html = "<html><head><title>Test</title></head><body><p>Hello, World!</p></body></html>"
    target_size_bytes = target_size_mb * 1024 * 1024  # Convert MB to bytes

    with open(file_name, 'w') as file:
        while file.tell() < target_size_bytes:
            file.write(sample_html)

generate_large_html("large_file.html", 10)  # Generates a 100MB HTML file
