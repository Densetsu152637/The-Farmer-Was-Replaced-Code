import heap

def extract_duplicate_max_values(petals):
    ret = []
    
    max = heap.heap_peek(petals)[0]
    
    while petals["size"] > 0:
        next = heap.heap_peek(petals)
        if next[0] < max:
            break
        ret.append(next)
        heap.heap_pop(petals)
        
    return ret
        
    
    
