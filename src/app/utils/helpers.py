from typing import List

def chunkify(lst:List, n:int) -> List[List[str]]:
    k, m = divmod(len(lst), n)
    return [lst[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n) if lst[i*k + min(i, m):(i+1)*k + min(i+1, m)]]
