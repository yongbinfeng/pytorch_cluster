from typing import Optional
import torch


def radius(x: torch.Tensor, y: torch.Tensor, r: float,
           batch_x: Optional[torch.Tensor] = None,
           batch_y: Optional[torch.Tensor] = None,
           max_num_neighbors: int = 32, n_threads: int = 1) -> torch.Tensor:
    r"""Finds for each element in :obj:`y` all points in :obj:`x` within
    distance :obj:`r`.

    Args:
        x (Tensor): Node feature matrix
            :math:`\mathbf{X} \in \mathbb{R}^{N \times F}`.
        y (Tensor): Node feature matrix
            :math:`\mathbf{Y} \in \mathbb{R}^{M \times F}`.
        r (float): The radius.
        batch_x (LongTensor, optional): Batch vector
            :math:`\mathbf{b} \in {\{ 0, \ldots, B-1\}}^N`, which assigns each
            node to a specific example. (default: :obj:`None`)
        batch_y (LongTensor, optional): Batch vector
            :math:`\mathbf{b} \in {\{ 0, \ldots, B-1\}}^M`, which assigns each
            node to a specific example. (default: :obj:`None`)
        max_num_neighbors (int, optional): The maximum number of neighbors to
            return for each element in :obj:`y`. (default: :obj:`32`)
        n_threads (int): number of threads when the input is on CPU.
            (default: :obj:`1`)

    .. code-block:: python

        import torch
        from torch_cluster import radius

        x = torch.Tensor([[-1, -1], [-1, 1], [1, -1], [1, 1]])
        batch_x = torch.tensor([0, 0, 0, 0])
        y = torch.Tensor([[-1, 0], [1, 0]])
        batch_y = torch.tensor([0, 0])
        assign_index = radius(x, y, 1.5, batch_x, batch_y)
    """

    x = x.view(-1, 1) if x.dim() == 1 else x
    y = y.view(-1, 1) if y.dim() == 1 else y

    if x.is_cuda:
        if batch_x is not None:
            assert x.size(0) == batch_x.numel()
            batch_size = int(batch_x.max()) + 1

            deg = x.new_zeros(batch_size, dtype=torch.long)
            deg.scatter_add_(0, batch_x, torch.ones_like(batch_x))

            ptr_x = deg.new_zeros(batch_size + 1)
            torch.cumsum(deg, 0, out=ptr_x[1:])
        else:
            ptr_x = None

        if batch_y is not None:
            assert y.size(0) == batch_y.numel()
            batch_size = int(batch_y.max()) + 1

            deg = y.new_zeros(batch_size, dtype=torch.long)
            deg.scatter_add_(0, batch_y, torch.ones_like(batch_y))
            ptr_y = deg.new_zeros(batch_size + 1)
            torch.cumsum(deg, 0, out=ptr_y[1:])
        else:
            ptr_y = None

        result = torch.ops.torch_cluster.radius(x, y, ptr_x, ptr_y, r,
                                                max_num_neighbors, n_threads)
    else:

        assert x.dim() == 2
        if batch_x is not None:
            assert batch_x.dim() == 1
            assert x.size(0) == batch_x.size(0)

        assert y.dim() == 2
        if batch_y is not None:
            assert batch_y.dim() == 1
            assert y.size(0) == batch_y.size(0)
        assert x.size(1) == y.size(1)

        result = torch.ops.torch_cluster.radius(x, y, batch_x, batch_y, r,
                                                max_num_neighbors, n_threads)

    return result


def radius_graph(x: torch.Tensor, r: float,
                 batch: Optional[torch.Tensor] = None, loop: bool = False,
                 max_num_neighbors: int = 32,
                 flow: str = 'source_to_target',
                 n_threads: int = 1) -> torch.Tensor:
    r"""Computes graph edges to all points within a given distance.

    Args:
        x (Tensor): Node feature matrix
            :math:`\mathbf{X} \in \mathbb{R}^{N \times F}`.
        r (float): The radius.
        batch (LongTensor, optional): Batch vector
            :math:`\mathbf{b} \in {\{ 0, \ldots, B-1\}}^N`, which assigns each
            node to a specific example. (default: :obj:`None`)
        loop (bool, optional): If :obj:`True`, the graph will contain
            self-loops. (default: :obj:`False`)
        max_num_neighbors (int, optional): The maximum number of neighbors to
            return for each element in :obj:`y`. (default: :obj:`32`)
        flow (string, optional): The flow direction when using in combination
            with message passing (:obj:`"source_to_target"` or
            :obj:`"target_to_source"`). (default: :obj:`"source_to_target"`)
        n_threads (int): number of threads when the input is on CPU.
            (default: :obj:`1`)

    :rtype: :class:`LongTensor`

    .. code-block:: python

        import torch
        from torch_cluster import radius_graph

        x = torch.Tensor([[-1, -1], [-1, 1], [1, -1], [1, 1]])
        batch = torch.tensor([0, 0, 0, 0])
        edge_index = radius_graph(x, r=1.5, batch=batch, loop=False)
    """

    assert flow in ['source_to_target', 'target_to_source']
    row, col = radius(x, x, r, batch, batch,
                      max_num_neighbors if loop else max_num_neighbors + 1,
                      n_threads)

    if x.is_cuda:
        row, col = (col, row) if flow == 'source_to_target' else (row, col)
    else:
        row, col = (col, row) if flow == 'target_to_source' else (row, col)

    if not loop:
        mask = row != col
        row, col = row[mask], col[mask]
    return torch.stack([row, col], dim=0)
