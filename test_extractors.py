from extractors import process_file_for_embedding

# Test na pliku tekstowym/obrazie/PDF
chunki = process_file_for_embedding("C:/Users/Szymon/Downloads/NET.pdf")
print(f"Wygenerowano {len(chunki)} chunków.")
for idx, chunk in enumerate(chunki[:3]):
    print(f"--- Chunk {idx + 1} ---")
    print(chunk)