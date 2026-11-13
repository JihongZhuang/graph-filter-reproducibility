"""Convert fixed processed test interactions to CSR."""
import numpy as np
import scipy.sparse as sp


def _pos_to_csr(pos: dict, shape) -> sp.csr_matrix:
    rows, cols = [], []
    for u, its in pos.items():
        rows.extend([u] * len(its)); cols.extend(its)
    return sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=shape, dtype=np.float64)
