from itertools import product

import pytest
import torch
from torch_cluster import radius, radius_graph
from .utils import grad_dtypes, devices, tensor
import pickle


def coalesce(index):
    N = index.max().item() + 1
    tensor = torch.sparse_coo_tensor(index, index.new_ones(index.size(1)),
                                     torch.Size([N, N]))
    return tensor.coalesce().indices()


@pytest.mark.parametrize('dtype,device', product(grad_dtypes, devices))
def test_radius(dtype, device):
    x = tensor([
        [-1, -1],
        [-1, +1],
        [+1, +1],
        [+1, -1],
        [-1, -1],
        [-1, +1],
        [+1, +1],
        [+1, -1],
    ], dtype, device)
    y = tensor([
        [0, 0],
        [0, 1],
    ], dtype, device)

    batch_x = tensor([0, 0, 0, 0, 1, 1, 1, 1], torch.long, device)
    batch_y = tensor([0, 1], torch.long, device)

    out = radius(x, y, 2, batch_x, batch_y, max_num_neighbors=4)
    assert coalesce(out).tolist() == [[0, 0, 0, 0, 1, 1], [0, 1, 2, 3, 5, 6]]


@pytest.mark.parametrize('dtype,device', product(grad_dtypes, devices))
def test_radius_graph(dtype, device):
    x = tensor([
        [-1.0, -1.0],
        [-1.0, +1.0],
        [+1.0, +1.0],
        [+1.0, -1.0],
    ], dtype, device)

    row, col = radius_graph(x, r=2, flow='target_to_source')
    col = col.view(-1, 2).sort(dim=-1)[0].view(-1)
    assert row.tolist() == [0, 0, 1, 1, 2, 2, 3, 3]
    assert col.tolist() == [1, 3, 0, 2, 1, 3, 0, 2]

    row, col = radius_graph(x, r=2, flow='source_to_target')
    row = row.view(-1, 2).sort(dim=-1)[0].view(-1)
    assert row.tolist() == [1, 3, 0, 2, 1, 3, 0, 2]
    assert col.tolist() == [0, 0, 1, 1, 2, 2, 3, 3]


@pytest.mark.parametrize('dtype,device', product(grad_dtypes, devices))
def test_radius_graph_pointnet_small(dtype, device):
    x = tensor([[0.2108, 0.4500, 0.8108],
                [-0.2332, 0.3985, 0.8528],
                [-0.2775, -0.3740, -0.1187],
                [-0.1254, 0.3485, 0.5012],
                [-0.1781, -0.1049, 0.3394],
                [0.1526, -0.3718, 0.3394],
                [-0.0544, 0.4183, 0.9912],
                [-0.1490, 0.3866, 0.7689],
                [-0.2845, -0.3310, 0.1143],
                [-0.1204, 0.4521, 0.8257],
                [0.2967, 0.4197, 0.9101],
                [0.2963, 0.4398, 0.9158],
                [-0.0125, -0.8122, 0.0335],
                [-0.2287, -0.3621, -0.7152],
                [0.1552, 0.0293, 0.4112],
                [-0.1401, -0.8694, 0.0335],
                [-0.3149, -0.5765, -0.0264],
                [0.3324, -0.7056, -0.0264],
                [-0.1534, -0.3684, 0.0335],
                [-0.2079, 0.3677, 0.2303],
                [-0.3143, -0.6923, -0.0407],
                [-0.1147, -0.7468, -0.6810],
                [-0.0311, 0.2705, 0.7223],
                [0.1081, 0.0270, 0.1415],
                [-0.1530, -0.8644, -0.1013],
                [0.6482, 0.0973, 0.1577],
                [0.4516, 0.0249, 0.0786],
                [0.3632, 0.2255, 0.1577],
                [-0.1171, 0.5048, 0.1520],
                [0.0538, 1.0000, -0.3962],
                [-0.0750, 0.0821, 0.1577],
                [0.7979, 0.8418, 0.1225],
                [0.1155, 1.0000, 0.1379],
                [0.4076, 1.0000, -0.2864],
                [0.6952, 0.7443, 0.0786],
                [0.0086, 0.8644, -0.6780],
                [0.4699, 0.1373, 0.5841],
                [-0.1617, 0.1948, 0.0057],
                [-0.3257, -0.6694, -0.4746],
                [-0.2095, 0.8714, 0.1482],
                [-0.1199, 0.4595, -0.3244],
                [0.2812, -0.6382, -0.3244],
                [0.5017, -0.6939, 0.4479],
                [0.4120, -0.8335, 0.3682],
                [0.3566, -0.7789, -0.3244],
                [-0.2904, -0.1869, -0.3244],
                [-0.1890, -0.8423, 0.0057],
                [0.3787, 0.5441, -0.1557]], dtype, device)

    batch = tensor([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3,
                    3, 3, 3, 3, 3, 3, 3, 3], torch.long, device)

    row, col = radius_graph(x, r=0.2, flow='source_to_target', batch=batch)

    edges = set([(i, j) for (i, j) in zip(list(row.cpu().numpy()),
                                          list(col.cpu().numpy()))])

    truth_row = [10, 11, 7, 9, 9, 1, 9, 1, 6, 7, 0, 11, 0, 10, 15, 12, 20, 16,
                 34, 31, 44, 43, 42, 41]
    truth_col = [0, 0, 1, 1, 6, 7, 7, 9, 9, 9, 10, 10, 11, 11, 12, 15, 16, 20,
                 31, 34, 41, 42, 43, 44]

    truth = set([(i, j) for (i, j) in zip(truth_row, truth_col)])

    assert(truth == edges)


@pytest.mark.parametrize('dtype,device', product(grad_dtypes, devices))
def test_radius_graph_pointnet_medium(dtype, device):
    x = tensor([[-4.4043e-02, -5.7983e-01, -9.7623e-02],
                [3.0804e-01, -1.8622e-01, 1.9274e-01],
                [1.9475e-02, 1.4221e-01, -2.7513e-02],
                [1.2231e-01, 1.8757e-02, -3.0827e-02],
                [2.8174e-01, 9.4371e-01, -3.7868e-02],
                [-3.3236e-01, -4.4852e-01, -1.6271e-01],
                [2.4958e-02, -5.8395e-01, -4.7551e-02],
                [-7.8186e-02, 4.2777e-01, -1.6271e-01],
                [3.3085e-01, -4.6802e-01, 2.0720e-01],
                [2.0581e-01, 4.4242e-01, 2.3870e-01],
                [-3.0456e-02, -7.2156e-02, -2.7691e-01],
                [1.2031e-01, -5.8759e-01, 3.2058e-02],
                [3.0601e-01, 5.9611e-01, 1.6639e-01],
                [-6.4328e-01, -5.1151e-01, -1.4634e-01],
                [1.7828e-01, -4.9254e-02, 3.5978e-02],
                [-2.9514e-01, -3.5513e-01, -1.6588e-01],
                [6.1963e-02, -3.9553e-02, -3.2432e-01],
                [2.9479e-01, -1.2834e-01, 5.4388e-02],
                [-7.4315e-02, 9.8307e-01, -3.2098e-01],
                [3.0474e-01, 7.0636e-01, -1.1068e-01],
                [-4.8368e-01, -5.9097e-01, 3.7825e-02],
                [-1.2121e-01, -1.4650e-01, -1.7073e-01],
                [1.9211e-01, 7.6821e-02, 1.8061e-01],
                [1.6331e-01, 6.9012e-02, -2.8236e-02],
                [-1.1057e-01, -1.5881e-01, -1.7098e-01],
                [-2.3803e-01, 7.0286e-01, -1.3979e-01],
                [3.1751e-01, 1.7584e-02, 2.0985e-01],
                [6.0034e-02, -5.7922e-01, -9.1098e-02],
                [-6.8475e-01, -9.7682e-02, -3.2432e-01],
                [1.6659e-01, -4.9622e-01, -5.1318e-02],
                [-3.2701e-01, -4.7730e-01, 1.2881e-01],
                [2.1012e-01, -8.7334e-02, 1.7803e-01],
                [2.7983e-01, -3.7054e-02, -1.5182e-01],
                [1.8969e-01, 7.0485e-01, 1.5651e-01],
                [2.8540e-01, -5.1271e-01, -3.3813e-02],
                [1.7029e-01, 3.7308e-01, -6.3154e-02],
                [1.9433e-01, -7.9255e-02, -5.8674e-02],
                [-1.4680e-01, 9.0324e-01, 2.0574e-02],
                [2.8562e-01, 3.2440e-02, -3.5898e-02],
                [-1.7669e-01, -4.3748e-02, -1.5858e-01],
                [-1.8106e-02, 8.9270e-01, -9.8274e-02],
                [-7.3858e-01, -4.9120e-01, -2.6034e-03],
                [1.3995e-01, 4.0296e-01, -3.2432e-01],
                [2.8693e-01, 5.7881e-01, -2.8429e-02],
                [8.4418e-02, 8.9270e-01, -1.0944e-01],
                [-2.2409e-01, 5.8757e-01, -2.3634e-01],
                [2.8154e-01, 2.2791e-01, -1.6294e-01],
                [-6.3224e-01, -4.8892e-01, 1.9713e-01],
                [-1.7948e-01, -5.6751e-01, 2.5630e-01],
                [-6.8280e-02, 2.8193e-01, -1.6271e-01],
                [8.6932e-02, -4.6200e-01, 1.9654e-02],
                [2.4729e-01, 7.7544e-01, -3.2432e-01],
                [1.6294e-01, 7.2947e-01, -6.0069e-02],
                [1.6623e-01, 7.0351e-01, -3.9932e-03],
                [2.2792e-02, 4.4052e-01, -1.6035e-01],
                [2.1738e-01, -5.9662e-01, -2.0707e-01],
                [1.7814e-01, -4.9335e-01, 2.0165e-01],
                [-4.8512e-01, -5.7955e-01, -1.0108e-01],
                [-3.2409e-01, -1.8065e-01, -1.7123e-01],
                [2.8822e-01, -4.3429e-01, -7.2851e-03],
                [-1.1018e-01, -2.6267e-01, -1.6717e-01],
                [2.0082e-01, 4.2539e-01, 1.4322e-01],
                [1.6313e-01, 1.2146e-01, -7.6836e-02],
                [-4.6902e-03, -5.6606e-01, 2.5757e-01],
                [2.5186e-02, -9.2425e-01, -1.2439e-01],
                [9.0190e-02, -3.8543e-01, -3.0639e-02],
                [3.0500e-01, 4.9113e-01, 1.5575e-01],
                [-4.7773e-01, -1.7712e-01, -1.2046e-01],
                [-3.5994e-01, -3.8259e-01, -3.2411e-02],
                [-4.2129e-01, -6.2995e-01, 6.4865e-02],
                [-4.3695e-01, -7.5720e-01, -1.3847e-01],
                [3.0692e-01, -4.3793e-02, 2.0492e-01],
                [2.2872e-01, -6.3545e-01, -3.0639e-02],
                [-2.0786e-01, 2.5038e-01, -3.2411e-02],
                [-4.8664e-01, 4.0222e-01, -1.0370e-01],
                [-1.9203e-01, -3.7129e-01, -1.2439e-01],
                [4.0446e-01, -2.8067e-01, -1.0378e-01],
                [2.1059e-01, 9.2508e-01, -1.2439e-01],
                [-1.9723e-01, 2.4433e-01, -3.0639e-02],
                [-3.1944e-01, -1.3357e-01, 6.4865e-02],
                [-2.6128e-01, -2.9865e-02, 6.4865e-02],
                [-2.6348e-01, 7.5135e-01, -1.2439e-01],
                [-2.8745e-01, 9.4139e-02, -1.2439e-01],
                [2.8162e-01, -1.0000e+00, 1.2521e-01],
                [1.8000e-01, -1.1031e-01, 6.8989e-02],
                [-9.7091e-02, 8.2881e-01, 1.6214e-01],
                [2.4762e-01, -7.0979e-02, -3.0639e-02],
                [3.1566e-01, -9.9768e-02, 2.9613e-01],
                [2.4752e-01, 5.3690e-01, -1.2439e-01],
                [-3.8513e-01, 2.4669e-01, 6.4865e-02],
                [2.2998e-01, -4.9642e-02, -1.2439e-01],
                [-4.5175e-01, -3.2219e-01, 6.3611e-02],
                [7.1355e-02, -6.7209e-01, 6.3499e-02],
                [3.7264e-01, 7.5637e-01, -1.2439e-01],
                [-3.5348e-01, 9.7893e-01, 1.4849e-01],
                [1.0323e-01, 5.5731e-01, 6.4865e-02],
                [1.8360e-01, -9.0216e-01, 1.6214e-01],
                [2.7071e-01, -6.9052e-01, -1.2439e-01],
                [4.0446e-01, -3.9623e-02, -7.8365e-02],
                [2.8596e-01, -1.0000e+00, -7.9833e-02],
                [4.4756e-02, 4.8919e-01, -1.2439e-01],
                [3.0237e-01, 2.1532e-01, 1.2105e-01],
                [2.8567e-01, 2.1856e-01, -2.0426e-02],
                [4.0446e-01, 2.3101e-01, 1.0086e-01],
                [-3.4453e-01, 4.4406e-01, -3.0639e-02],
                [-4.8664e-01, 6.1598e-01, -8.0291e-02],
                [2.6624e-01, -4.0841e-01, -2.9835e-02],
                [3.1751e-01, -3.5890e-01, 3.2058e-01],
                [4.0446e-01, -7.6102e-01, -5.2483e-02],
                [-1.7093e-01, -6.3454e-01, -1.2439e-01],
                [-1.1814e-01, 2.7095e-01, -1.2439e-01],
                [7.5540e-02, -9.8103e-01, -1.2383e-01],
                [4.0041e-01, -1.4177e-01, 1.5437e-01],
                [1.0351e-01, 3.8102e-01, -1.2439e-01],
                [3.0761e-01, -2.0948e-01, 1.9012e-01],
                [1.8582e-01, 4.5887e-01, 6.8633e-02],
                [2.4285e-01, 1.7587e-01, -1.2439e-01],
                [3.0026e-01, 6.6768e-01, 9.3234e-02],
                [2.8018e-01, -2.8312e-01, 6.7638e-02],
                [4.0413e-01, 6.2224e-01, 1.4709e-01],
                [2.1721e-01, -2.8875e-01, -3.2411e-02],
                [2.9549e-01, -1.9357e-01, 1.1317e-01],
                [4.3894e-02, 6.3914e-01, -3.0639e-02],
                [-4.3525e-01, 7.3082e-01, 1.3111e-01],
                [1.9329e-01, 7.3155e-01, 2.6939e-01],
                [3.0241e-01, 1.3610e-02, 2.0000e-01],
                [-4.8255e-01, 6.7159e-01, -1.1665e-01],
                [-4.0376e-01, 5.2112e-01, -1.2439e-01],
                [-2.1529e-01, -9.0250e-01, -1.8576e-01],
                [1.3653e-01, 6.0331e-01, -1.4182e-02],
                [-5.1030e-01, 5.2375e-01, -1.4160e-01],
                [9.3857e-02, 8.5117e-01, -1.8576e-01],
                [1.7257e-01, -7.1580e-01, 1.2117e-01],
                [-2.9819e-02, 8.6545e-01, -1.8576e-01],
                [-2.9166e-01, -8.3588e-01, 6.6004e-02],
                [1.7725e-01, 2.2532e-01, 2.6537e-01],
                [2.3682e-01, 4.0249e-01, -1.5797e-01],
                [-5.1030e-01, 3.2232e-01, -1.4140e-01],
                [2.1317e-01, 5.9061e-01, -1.4182e-02],
                [-5.1030e-01, -3.0540e-01, -1.0576e-01],
                [-4.2774e-01, 1.0000e+00, 7.8977e-02],
                [8.6148e-02, 9.2760e-01, -1.4182e-02],
                [-4.1586e-01, -8.1449e-01, 1.6100e-01],
                [1.8051e-01, 7.4713e-01, 9.9315e-02],
                [-4.4974e-01, 1.5543e-01, -1.8576e-01],
                [1.8339e-01, -2.2648e-01, 1.6155e-01],
                [-1.8434e-01, -7.9208e-01, 8.9535e-02],
                [2.3367e-01, -9.2556e-01, -1.8576e-01],
                [-3.6223e-01, 8.6446e-01, -1.8547e-01],
                [-7.7763e-02, -8.4014e-01, 8.9535e-02],
                [8.6664e-02, -2.2030e-02, -1.8576e-01],
                [1.3196e-01, 4.9885e-01, 9.6345e-02],
                [-3.9771e-01, 3.9167e-01, -1.4182e-02],
                [-3.3379e-01, -2.4647e-01, -1.4182e-02],
                [6.3328e-02, -5.9357e-01, -1.8576e-01],
                [-4.2640e-01, -7.4439e-01, -1.4182e-02],
                [2.3682e-01, -1.8300e-01, -9.5117e-02],
                [2.2544e-01, -6.9952e-01, 3.1850e-01],
                [4.8674e-02, 4.2719e-01, -1.8576e-01],
                [1.7041e-01, -5.5259e-03, 2.3983e-01],
                [1.0906e-01, -6.9281e-01, -1.8576e-01],
                [1.7104e-01, -8.0757e-02, 2.4217e-01],
                [1.7095e-01, 5.1883e-03, 1.3790e-01],
                [-4.1693e-01, -9.9418e-01, 1.2441e-01],
                [1.3677e-01, 6.2831e-01, 1.1430e-01],
                [1.7208e-01, -5.1367e-01, 1.1934e-01],
                [1.2066e-01, -6.9953e-01, 3.1373e-02],
                [2.3682e-01, 5.1519e-01, -9.3649e-02],
                [1.7667e-01, 6.2188e-01, 2.6320e-01],
                [-2.3054e-01, 9.4740e-01, -1.8576e-01],
                [-2.9772e-01, 7.9202e-01, 1.1509e-01],
                [-4.8740e-01, 8.6416e-01, -2.7967e-01],
                [2.3682e-01, 9.7401e-02, -1.1460e-01],
                [-3.7717e-01, -4.9797e-01, -1.8576e-01],
                [-1.4868e-01, 4.9006e-02, -1.8576e-01],
                [-3.6907e-01, 2.5399e-01, -1.4182e-02],
                [2.3682e-01, -7.3611e-01, -4.9100e-02],
                [1.5108e-01, -7.0813e-01, 1.6769e-01],
                [-5.1030e-01, 6.0329e-02, -1.3040e-01],
                [1.3562e-01, -8.8510e-01, 8.9535e-02],
                [-5.0098e-01, -9.4882e-01, -1.8576e-01],
                [2.2378e-02, 5.1602e-01, -1.8576e-01],
                [-4.4093e-01, -3.7677e-01, -1.4182e-02],
                [-3.3312e-02, -8.2281e-01, 1.6100e-01],
                [2.3682e-01, -3.7022e-01, -8.0912e-02],
                [-4.1024e-01, 1.6750e-01, -1.8576e-01],
                [-5.1030e-01, 6.2264e-01, -1.2082e-01],
                [4.7247e-02, -3.5037e-01, -1.4182e-02],
                [1.3448e-01, 1.6774e-03, 6.1691e-02],
                [2.0452e-01, 3.8128e-01, 3.6715e-01],
                [2.3765e-01, 6.1790e-01, 3.6407e-01],
                [1.0179e-01, 9.6686e-01, -1.4182e-02],
                [-1.4317e-01, -8.2904e-01, 1.3263e-01],
                [-3.8616e-01, -8.9195e-01, -5.1920e-02],
                [3.3982e-01, -6.1857e-01, 1.3609e-01],
                [-9.7382e-02, 1.0669e-01, 1.2561e-01],
                [-5.1578e-02, -1.8835e-01, -5.8711e-02],
                [-2.7611e-01, 3.1850e-01, 1.4525e-01],
                [1.1082e-01, 5.5939e-01, 1.3517e-01],
                [-3.9811e-01, 1.9702e-01, 8.2159e-02],
                [-4.2162e-01, 1.2716e-01, -5.2557e-02],
                [-4.1794e-01, -4.3431e-01, 3.1557e-02],
                [-2.3018e-01, 5.3723e-01, -5.8711e-02],
                [3.0747e-01, 4.8079e-01, 1.4079e-01],
                [-4.0380e-01, 6.2203e-01, 1.2976e-02],
                [1.3282e-01, 7.1973e-01, 2.1321e-01],
                [-4.1427e-01, 2.9916e-01, 3.2114e-02],
                [-3.3050e-02, -7.6029e-01, 1.3022e-01],
                [-5.6017e-02, 2.1223e-01, 1.2740e-01],
                [-1.7645e-01, 3.6704e-02, 1.1948e-01],
                [-3.3695e-01, 6.4689e-01, -5.8711e-02],
                [2.5100e-01, -6.9047e-01, 1.2395e-01],
                [6.1637e-02, -7.8208e-01, 1.3098e-01],
                [1.0924e-01, -3.4489e-01, 1.1948e-01],
                [-4.2138e-01, -2.7649e-01, 3.0480e-02],
                [2.8935e-01, 3.2112e-01, -5.8711e-02],
                [4.9335e-02, 1.0779e-01, 1.1948e-01],
                [-4.1153e-01, -9.8230e-01, -1.9865e-01],
                [-1.4141e-01, 2.7516e-01, 1.1948e-01],
                [-2.2923e-01, 5.5029e-01, 1.3529e-01],
                [-8.3756e-02, 6.7739e-01, 1.4031e-01],
                [-1.0300e-01, 9.8000e-01, 2.3907e-02],
                [9.6010e-02, 2.0017e-01, 1.4851e-01],
                [2.9399e-01, 1.3362e-01, 1.2795e-01],
                [-7.6118e-02, 4.6750e-01, 1.4116e-01],
                [2.1055e-01, -1.2122e-01, 1.5125e-01],
                [-4.0380e-01, -8.6360e-01, 1.2610e-02],
                [3.1182e-01, -3.0756e-01, 1.1948e-01],
                [-1.2531e-01, -6.6049e-01, 1.5181e-01],
                [3.9872e-01, 8.2265e-01, 3.9365e-02],
                [4.1678e-01, 2.0115e-01, -6.8050e-02],
                [-2.4971e-01, 4.1474e-01, 1.4261e-01],
                [-1.2480e-01, -4.5028e-01, 1.1985e-01],
                [3.5515e-01, 3.4642e-01, 1.4046e-01],
                [3.5099e-01, -3.7661e-01, -5.8711e-02],
                [-3.8801e-01, 7.2518e-01, -5.0083e-02],
                [3.8532e-01, -2.5975e-01, 1.0816e-01],
                [-1.0815e-01, -5.9211e-01, 1.5576e-01],
                [3.9896e-01, 5.9310e-01, -5.2468e-02],
                [-3.7451e-01, -4.4229e-01, 1.1878e-01],
                [1.4604e-01, -4.7458e-01, 1.5354e-01],
                [1.8387e-01, -5.1880e-01, 1.2019e-01],
                [-5.5425e-02, 3.0991e-01, 1.1948e-01],
                [3.2365e-01, 1.4492e-01, 1.4381e-01],
                [3.9883e-01, 5.3333e-01, 2.5506e-02],
                [-1.2786e-01, -1.6478e-01, -5.8711e-02],
                [2.2632e-01, -6.4876e-01, 1.2236e-01],
                [2.6546e-01, -8.1790e-01, 1.3022e-01],
                [-4.0153e-01, -8.1647e-01, 6.2641e-02],
                [2.2915e-01, -9.4253e-04, -5.8711e-02],
                [-2.6010e-01, 1.3121e-01, 1.5039e-01],
                [9.4847e-02, -3.8382e-01, 1.5446e-01],
                [-1.3159e-01, 8.5891e-01, -5.8711e-02],
                [3.1891e-01, -4.4107e-01, 1.4460e-01],
                [-1.2279e-01, 1.7300e-01, 1.4925e-01],
                [-4.0297e-01, -1.2408e-01, 1.1571e-02]], dtype, device)

    batch = tensor([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3,
                    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
                    3, 3, 3, 3, 3], torch.long, device)

    row, col = radius_graph(x, r=0.2, flow='source_to_target', batch=batch)

    edges = set([(i, j) for (i, j) in zip(list(row.cpu().numpy()),
                                          list(col.cpu().numpy()))])

    truth_row = [6, 27, 17, 31, 3, 23, 62, 2, 14, 23, 36, 38, 62, 15, 0, 11,
                 27, 29, 50, 49, 54, 56, 12, 61, 16, 21, 24, 39, 6, 27, 29,
                 34, 50, 9, 33, 43, 41, 57, 3, 17, 22, 23, 31, 36, 38, 5, 58,
                 10, 1, 14, 31, 36, 38, 43, 52, 53, 57, 10, 24, 39, 60, 14,
                 26, 31, 2, 3, 14, 36, 38, 62, 10, 21, 39, 60, 45, 22, 31, 0,
                 6, 11, 29, 50, 55, 6, 11, 27, 34, 50, 55, 59, 1, 14, 17, 22,
                 26, 36, 38, 12, 53, 11, 29, 59, 54, 3, 14, 17, 23, 32, 38,
                 40, 3, 14, 17, 23, 32, 36, 62, 10, 21, 24, 37, 44, 13, 12,
                 19, 52, 53, 40, 52, 25, 62, 63, 7, 54, 6, 11, 27, 29, 19, 43,
                 44, 53, 19, 33, 43, 52, 7, 35, 49, 27, 29, 8, 13, 20, 15, 29,
                 34, 21, 24, 9, 2, 3, 23, 38, 46, 48, 111, 106, 120, 115, 117,
                 119, 75, 91, 84, 87, 112, 114, 121, 125, 92, 97, 78, 82, 110,
                 104, 127, 68, 73, 82, 110, 80, 79, 73, 78, 96, 71, 86, 118,
                 121, 84, 90, 98, 121, 71, 112, 114, 125, 86, 98, 68, 72, 115,
                 122, 83, 72, 108, 86, 90, 113, 122, 102, 103, 101, 103, 116,
                 101, 102, 74, 127, 126, 127, 65, 118, 120, 114, 97, 73, 78,
                 64, 71, 87, 114, 121, 125, 100, 71, 87, 107, 112, 118, 121,
                 66, 95, 102, 66, 119, 84, 106, 114, 120, 121, 66, 117, 65,
                 106, 118, 121, 71, 84, 86, 112, 114, 118, 120, 95, 100, 71,
                 87, 112, 105, 127, 74, 104, 105, 126, 138, 143, 151, 164, 167,
                 186, 133, 141, 166, 176, 177, 179, 131, 142, 146, 155, 189,
                 158, 167, 144, 152, 185, 129, 143, 151, 164, 167, 182, 131,
                 191, 134, 155, 163, 129, 138, 164, 137, 178, 185, 161, 134,
                 149, 183, 169, 171, 146, 183, 129, 138, 164, 137, 175, 182,
                 160, 134, 142, 184, 177, 136, 181, 161, 162, 188, 154, 176,
                 145, 159, 162, 159, 161, 188, 142, 129, 138, 143, 151, 168,
                 132, 176, 177, 179, 129, 136, 138, 164, 190, 148, 148, 152,
                 185, 132, 160, 166, 132, 157, 166, 179, 144, 185, 132, 166,
                 177, 183, 158, 139, 153, 146, 149, 179, 156, 137, 144, 175,
                 178, 130, 159, 162, 135, 168, 141, 207, 228, 217, 226, 248,
                 211, 241, 246, 253, 208, 209, 216, 218, 250, 254, 245, 199,
                 206, 218, 231, 250, 205, 197, 200, 206, 250, 199, 206, 214,
                 239, 210, 219, 233, 244, 210, 235, 198, 197, 199, 200, 192,
                 212, 228, 237, 195, 216, 218, 222, 242, 254, 195, 250, 254,
                 202, 204, 235, 194, 241, 246, 247, 207, 240, 241, 251, 201,
                 239, 255, 230, 195, 208, 222, 254, 193, 195, 197, 208, 231,
                 242, 250, 254, 202, 220, 224, 231, 219, 252, 208, 216, 242,
                 243, 219, 231, 242, 193, 248, 234, 236, 253, 192, 207, 237,
                 215, 197, 218, 219, 224, 237, 203, 227, 204, 210, 227, 253,
                 207, 228, 232, 244, 201, 214, 213, 241, 246, 251, 253, 194,
                 211, 213, 240, 246, 251, 253, 208, 218, 222, 224, 254, 223,
                 203, 238, 196, 194, 211, 240, 241, 247, 211, 246, 193, 226,
                 195, 197, 199, 209, 218, 254, 213, 240, 241, 221, 194, 227,
                 236, 240, 241, 195, 208, 209, 216, 218, 242, 250, 214]
    truth_col = [0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 3, 5, 6, 6, 6, 6, 6, 7,
                 7, 8, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11, 11, 12, 12, 12,
                 13, 13, 14, 14, 14, 14, 14, 14, 14, 15, 15, 16, 17, 17, 17,
                 17, 17, 19, 19, 19, 20, 21, 21, 21, 21, 22, 22, 22, 23, 23,
                 23, 23, 23, 23, 24, 24, 24, 24, 25, 26, 26, 27, 27, 27,
                 27, 27, 27, 29, 29, 29, 29, 29, 29, 29, 31, 31, 31, 31,
                 31, 32, 32, 33, 33, 34, 34, 34, 35, 36, 36, 36, 36, 36, 36,
                 37, 38, 38, 38, 38, 38, 38, 38, 39, 39, 39, 40, 40, 41, 43,
                 43, 43, 43, 44, 44, 45, 46, 48, 49, 49, 50, 50, 50, 50, 52,
                 52, 52, 52, 53, 53, 53, 53, 54, 54, 54, 55, 55, 56, 57, 57,
                 58, 59, 59, 60, 60, 61, 62, 62, 62, 62, 62, 63, 64, 65, 65,
                 66, 66, 66, 68, 68, 71, 71, 71, 71, 71, 71, 72, 72, 73, 73,
                 73, 74, 74, 75, 78, 78, 78, 79, 80, 82, 82, 83, 84, 84, 84,
                 84, 86, 86, 86, 86, 87, 87, 87, 87, 90, 90, 91, 92, 95, 95,
                 96, 97, 97, 98, 98, 100, 100, 101, 101, 102, 102, 102, 103,
                 103, 104, 104, 105, 105, 106, 106, 106, 107, 108, 110, 110,
                 111, 112, 112, 112, 112, 112, 113, 114, 114, 114, 114, 114,
                 114, 115, 115, 116, 117, 117, 118, 118, 118, 118, 118, 119,
                 119, 120, 120, 120, 120, 121, 121, 121, 121, 121, 121, 121,
                 122, 122, 125, 125, 125, 126, 126, 127, 127, 127, 127, 129,
                 129, 129, 129, 129, 130, 131, 131, 132, 132, 132, 132, 133,
                 134, 134, 134, 135, 136, 136, 137, 137, 137, 138, 138, 138,
                 138, 138, 139, 141, 141, 142, 142, 142, 143, 143, 143, 144,
                 144, 144, 145, 146, 146, 146, 148, 148, 149, 149, 151, 151,
                 151, 152, 152, 153, 154, 155, 155, 156, 157, 158, 158, 159,
                 159, 159, 160, 160, 161, 161, 161, 162, 162, 162, 163, 164,
                 164, 164, 164, 164, 166, 166, 166, 166, 167, 167, 167, 168,
                 168, 169, 171, 175, 175, 176, 176, 176, 177, 177, 177, 177,
                 178, 178, 179, 179, 179, 179, 181, 182, 182, 183, 183, 183,
                 184, 185, 185, 185, 185, 186, 188, 188, 189, 190, 191, 192,
                 192, 193, 193, 193, 194, 194, 194, 194, 195, 195, 195, 195,
                 195, 195, 196, 197, 197, 197, 197, 197, 198, 199, 199, 199,
                 199, 200, 200, 201, 201, 202, 202, 203, 203, 204, 204, 205,
                 206, 206, 206, 207, 207, 207, 207, 208, 208, 208, 208, 208,
                 208, 209, 209, 209, 210, 210, 210, 211, 211, 211, 211, 212,
                 213, 213, 213, 214, 214, 214, 215, 216, 216, 216, 216, 217,
                 218, 218, 218, 218, 218, 218, 218, 219, 219, 219, 219, 220,
                 221, 222, 222, 222, 223, 224, 224, 224, 226, 226, 227, 227,
                 227, 228, 228, 228, 230, 231, 231, 231, 231, 232, 233, 234,
                 235, 235, 236, 236, 237, 237, 237, 238, 239, 239, 240, 240,
                 240, 240, 240, 241, 241, 241, 241, 241, 241, 241, 242, 242,
                 242, 242, 242, 243, 244, 244, 245, 246, 246, 246, 246, 246,
                 247, 247, 248, 248, 250, 250, 250, 250, 250, 250, 251, 251,
                 251, 252, 253, 253, 253, 253, 253, 254, 254, 254, 254, 254,
                 254, 254, 255]

    truth = set([(i, j) for (i, j) in zip(truth_row, truth_col)])
    assert(truth == edges)


@pytest.mark.parametrize('dtype,device', product(grad_dtypes, devices))
def test_radius_graph_ndim(dtype, device):
    x = tensor([[-0.9750, -0.7160, 0.7150, -0.1510, -0.3660, 0.6140, -1.0340,
                2.4950],
                [0.8540, 0.1110, 1.0520, -1.3900, 0.7570, -0.6300, -0.9550,
                -0.9350],
                [0.3710, 0.4610, 0.1620, 1.1370, -1.5830, 0.4100, -0.5710,
                -0.7760],
                [0.4200, 0.1240, -1.2870, -0.2300, -1.7480, 0.5890, 0.5710,
                0.1670],
                [-0.6060, 0.8080, -2.2560, 0.4480, -0.8910, 0.2360, -0.0060,
                -0.6510],
                [-0.6960, 0.7190, -0.7330, 0.4660, 0.4400, -0.0490, -1.1350,
                -0.5990],
                [-0.0080, -0.4770, 0.0980, 1.2000, -0.6110, -0.7410, 0.7410,
                -0.2800],
                [-2.5230, -0.8470, -0.8670, 0.4820, -0.9510, -0.9460, 0.3390,
                -1.6740],
                [1.0770, -1.4480, 1.8110, 0.0900, 0.7980, 0.4070, 1.9570,
                -0.2010],
                [1.0890, -0.2150, -0.4440, 0.4370, 1.1180, -0.4280, -2.3860,
                0.5860],
                [0.1000, -0.2590, -2.1420, 0.9260, 0.7290, -0.1170, 0.9370,
                -0.0470],
                [-0.3870, -1.7310, -0.6020, -0.1070, 1.7890, 0.5200, 1.2620,
                0.6130],
                [-0.0740, 0.5270, 0.4090, -0.9120, -0.1690, 1.4970, -2.4540,
                -1.0430],
                [-0.9750, -1.3510, 0.0730, 0.1450, -0.9910, -1.8840, 0.1010,
                0.4620],
                [0.6950, 0.3560, 0.2850, -0.1050, -1.8770, 1.4910, 2.0260,
                -0.8170],
                [-1.3480, 0.1100, 0.8460, -0.1050, -1.9670, -0.0930, 0.2820,
                1.7150],
                [-0.0340, -0.7420, 0.5450, 1.8170, -0.6030, -0.0990, 0.1650,
                -0.0450],
                [0.4490, 1.6170, -1.6880, -0.6180, -0.8350, 1.0560, -0.3860,
                0.8380],
                [0.9530, -0.1970, -0.7030, 1.7750, -1.6860, -1.4290, 0.6280,
                0.2730],
                [0.6630, 1.0780, 1.5650, -0.5490, -0.5530, -0.8070, 0.4100,
                -2.4380],
                [0.6350, 0.0490, 0.1990, -1.2340, 0.7630, 0.2670, 1.5810,
                -0.4250],
                [1.6700, 0.4440, -2.5800, 0.5020, 0.3520, -0.9110, -1.9960,
                -0.0000],
                [0.1970, 0.2390, 2.2290, -0.0910, 1.2710, 0.0280, -0.5530,
                -1.4650],
                [0.1270, 2.5150, -0.3450, -0.8340, 1.0130, -1.3680, -0.1990,
                -0.5480],
                [-1.0470, 0.0200, 2.2200, 1.7030, 0.5460, 0.4350, -1.8560,
                -0.9750],
                [0.7010, -0.7260, -0.2380, 0.6120, 1.1150, -1.2530, -0.2140,
                1.0100],
                [-0.2590, -0.2690, 0.1200, 1.0380, -0.8370, -0.0070, -0.0800,
                0.2130],
                [-0.5460, 0.4000, 0.2040, -0.8370, 1.7400, 1.0940, 0.0930,
                -0.3370],
                [-1.0230, 1.5400, 0.9760, -1.5210, 1.0170, -1.3290, 0.7690,
                0.6260],
                [-0.7560, 0.1360, -0.2640, -0.6130, -0.2830, 0.6830, -0.8700,
                -0.5610],
                [0.4060, 0.3830, 2.4530, -0.4910, -1.3110, -0.0980, -0.0630,
                0.3200],
                [0.1450, 0.5810, -0.7310, 0.8190, -1.3600, -0.6780, -0.3360,
                -0.2570]], dtype, device)

    batch = tensor([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 4, 4, 4, 4, 5,
                    5, 5, 5, 6, 6, 6, 6, 6, 7, 7, 8, 9], torch.long, device)

    row, col = radius_graph(x, r=4.4, flow='source_to_target', batch=batch)

    edges = set([(i, j) for (i, j) in zip(list(row.cpu().numpy()),
                                          list(col.cpu().numpy()))])

    truth_row = [2, 3, 2, 3, 0, 1, 3, 4, 0, 1, 2, 4, 2, 3, 6, 7, 9, 10, 5, 7,
                 8, 9, 10, 5, 6, 10, 6, 5, 6, 10, 5, 6, 7, 9, 13, 11, 16, 17,
                 18, 15, 17, 18, 15, 16, 18, 15, 16, 17, 20, 22, 19, 22, 19,
                 20, 25, 26, 27, 26, 27, 23, 26, 27, 23, 24, 25, 27, 23, 24,
                 25, 26, 29, 28]
    truth_col = [0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 5, 5, 5, 5, 6, 6,
                 6, 6, 6, 7, 7, 7, 8, 9, 9, 9, 10, 10, 10, 10, 11, 13, 15, 15,
                 15, 16, 16, 16, 17, 17, 17, 18, 18, 18, 19, 19, 20, 20, 22,
                 22, 23, 23, 23, 24, 24, 25, 25, 25, 26, 26, 26, 26, 27, 27,
                 27, 27, 28, 29]

    truth = set([(i, j) for (i, j) in zip(truth_row, truth_col)])

    assert(truth == edges)


@pytest.mark.parametrize('dtype,device', product(grad_dtypes, devices))
def test_radius_graph_large(dtype, device):
    d = pickle.load(open("test/radius_test_large.pkl", "rb"))
    x = d['x'].to(device)
    r = d['r']
    truth = d['edges']

    row, col = radius_graph(x, r=r, flow='source_to_target',
                            batch=None, n_threads=24)

    edges = set([(i, j) for (i, j) in zip(list(row.cpu().numpy()),
                                          list(col.cpu().numpy()))])

    assert(truth == edges)

    row, col = radius_graph(x, r=r, flow='source_to_target',
                            batch=None, n_threads=12)

    edges = set([(i, j) for (i, j) in zip(list(row.cpu().numpy()),
                                          list(col.cpu().numpy()))])

    assert(truth == edges)

    row, col = radius_graph(x, r=r, flow='source_to_target',
                            batch=None, n_threads=1)

    edges = set([(i, j) for (i, j) in zip(list(row.cpu().numpy()),
                                          list(col.cpu().numpy()))])

    assert(truth == edges)
