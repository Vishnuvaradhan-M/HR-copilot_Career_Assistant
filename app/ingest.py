# app/ingest.py
import pdfplumber
import uuid
import re


def extract_text_from_pdf(path):
    """
    Extract all text from PDF using pdfplumber.
    Returns full document text preserving page boundaries.
    """
    pages_data = []
    
    try:
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                # Join broken lines and normalize whitespace
                text = re.sub(r'-\n', '', text)  # Remove hyphens at line breaks
                text = re.sub(r'\n', ' ', text)   # Convert newlines to spaces
                text = re.sub(r'\s+', ' ', text).strip()  # Normalize spaces
                
                if text:
                    pages_data.append({"page": page_num, "text": text})
    
    except Exception as e:
        print(f"[ERROR] PDF extraction failed: {e}")
        return []
    
    return pages_data


def identify_clause_boundaries(text):
    """
    Identify clause and section boundaries in policy text.
    
    Returns list of tuples (start_pos, end_pos, is_header, level)
    where level indicates header hierarchy (0=top, 1=subsection, etc.)
    """
    boundaries = []
    
    # Pattern for numbered sections: 1.2.3 or 1.2 or just 1
    section_pattern = re.compile(
        r'(?:^|\s)'  # Start of string or whitespace
        r'(\d+(?:\.\d+)*)'  # Section number
        r'(?:\s+|\.?\s+)'  # Space/dot separator
        r'([A-Z][^.!?]*[.!?])',  # Title (capital letter start)
        re.MULTILINE
    )
    
    # Pattern for bullet points and numbered lists
    bullet_pattern = re.compile(
        r'(?:^|\s)'
        r'(?:[-•*]|\d+\))'  # Bullet or number
        r'\s+'
        r'([A-Z][^.!?\n]*[.!?])',
        re.MULTILINE
    )
    
    for match in section_pattern.finditer(text):
        section_num = match.group(1)
        title = match.group(2)
        # Determine header level by counting dots
        level = len(section_num.split('.')) - 1
        boundaries.append({
            'pos': match.start(),
            'type': 'section',
            'level': level,
            'marker': section_num,
            'text': f"{section_num} {title}"
        })
    
    for match in bullet_pattern.finditer(text):
        boundaries.append({
            'pos': match.start(),
            'type': 'bullet',
            'level': 2,
            'marker': match.group(0)[:10],
            'text': match.group(1)
        })
    
    return boundaries


def split_by_clauses(text, page_num):
    """
    Split text into chunks based on clause/section boundaries.
    
    Args:
        text: Full text for one or more pages
        page_num: Current page number
    
    Returns:
        List of chunk dicts
    """
    if not text or len(text) < 100:
        return []
    
    chunks = []
    boundaries = identify_clause_boundaries(text)
    
    # If no boundaries found, split by natural paragraph breaks
    if not boundaries:
        # Split on multiple spaces (paragraph breaks preserved in original)
        para_pattern = re.compile(r'\.(?:\s{2,}|\n\n)')
        paragraphs = para_pattern.split(text)
        
        for para in paragraphs:
            para = para.strip()
            if len(para) >= 100:  # Only keep substantial paragraphs
                chunks.append({
                    'text': para,
                    'page': page_num,
                    'type': 'paragraph'
                })
        
        return chunks
    
    # Sort boundaries by position
    boundaries.sort(key=lambda x: x['pos'])
    
    # Create chunks at each boundary
    for i, boundary in enumerate(boundaries):
        # Start position is after the boundary marker
        start_pos = boundary['pos']
        
        # End position is at the next boundary (or end of text)
        if i < len(boundaries) - 1:
            end_pos = boundaries[i + 1]['pos']
        else:
            end_pos = len(text)
        
        chunk_text = text[start_pos:end_pos].strip()
        
        # Keep all chunks >= 50 chars (include short clauses)
        if len(chunk_text) >= 50:
            chunks.append({
                'text': chunk_text,
                'page': page_num,
                'type': boundary['type'],
                'marker': boundary.get('marker', ''),
                'level': boundary.get('level', 0)
            })
    
    return chunks


def merge_short_chunks(chunks, min_length=100):
    """
    Merge short chunks with following chunk to avoid fragmentation.
    CRITICAL: Never merge atomic numbered clauses (e.g., 5.2.2).
    Preserves all text while improving chunk coherence.
    """
    if not chunks:
        return chunks
    
    # Pattern to detect if a chunk is an atomic numbered clause
    atomic_clause_pattern = re.compile(r'^\d+(?:\.\d+)+\s')
    
    merged = []
    i = 0
    
    while i < len(chunks):
        current = chunks[i].copy()
        is_atomic = bool(atomic_clause_pattern.match(current['text']))
        
        # Only merge if current is NOT an atomic clause AND it's too short
        # Atomic clauses are never merged, regardless of length
        while not is_atomic and len(current['text']) < min_length and i + 1 < len(chunks):
            i += 1
            next_chunk = chunks[i]
            current['text'] = current['text'] + " " + next_chunk['text']
            # Keep page from first chunk
        
        merged.append(current)
        i += 1
    
    return merged


def extract_and_chunk(path):
    """
    Extract text from PDF and split into clause-aligned chunks.
    
    Returns:
        List of dicts with keys: chunk_id, page, index, text
    """
    # Extract text page by page
    pages_data = extract_text_from_pdf(path)
    
    if not pages_data:
        return []
    
    # Process each page for clause boundaries
    all_chunks = []
    for page_data in pages_data:
        page_chunks = split_by_clauses(page_data['text'], page_data['page'])
        all_chunks.extend(page_chunks)
    
    if not all_chunks:
        return []
    
    # Merge very short chunks to improve coherence
    all_chunks = merge_short_chunks(all_chunks, min_length=100)
    
    # Create final chunk objects with UUIDs and indices
    result = []
    for idx, chunk in enumerate(all_chunks):
        result.append({
            "chunk_id": str(uuid.uuid4()),
            "page": chunk['page'],
            "index": idx,
            "text": chunk['text']
        })
    
    return result
