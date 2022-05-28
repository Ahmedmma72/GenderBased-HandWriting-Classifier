import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np


# for cold feature
N_RHO_BINS = 7
N_ANGLE_BINS = 12
N_BINS = N_RHO_BINS * N_ANGLE_BINS
BIN_SIZE = 360 // N_ANGLE_BINS
R_INNER = 5.0
R_OUTER = 35.0
K_S = np.arange(3, 8)


def get_contour_pixels(bw_image):
    contours, _ = cv.findContours(
        bw_image, cv.RETR_TREE,
        cv.CHAIN_APPROX_NONE
    )
    contours = sorted(contours, key=cv.contourArea, reverse=True)[1:]
    return contours


# very bad accuracy for this feature
def get_cold_features(bw_image, approx_poly_factor=0.01):

    contours = get_contour_pixels(bw_image)

    rho_bins_edges = np.log10(np.linspace(R_INNER, R_OUTER, N_RHO_BINS))
    feature_vectors = np.zeros((len(K_S), N_BINS))

    # print([len(cnt) for cnt in contours])
    for j, k in enumerate(K_S):
        hist = np.zeros((N_RHO_BINS, N_ANGLE_BINS))
        for cnt in contours:
            epsilon = approx_poly_factor * cv.arcLength(cnt, True)
            cnt = cv.approxPolyDP(cnt, epsilon, True)
            n_pixels = len(cnt)

            point_1s = np.array([point[0] for point in cnt])
            x1s, y1s = point_1s[:, 0], point_1s[:, 1]
            point_2s = np.array([cnt[(i + k) % n_pixels][0]
                                for i in range(n_pixels)])
            x2s, y2s = point_2s[:, 0], point_2s[:, 1]

            thetas = np.degrees(np.arctan2(y2s - y1s, x2s - x1s) + np.pi)
            rhos = np.sqrt((y2s - y1s) ** 2 + (x2s - x1s) ** 2)
            rhos_log_space = np.log10(rhos)

            quantized_rhos = np.zeros(rhos.shape, dtype=int)
            for i in range(N_RHO_BINS):
                quantized_rhos += (rhos_log_space < rho_bins_edges[i])

            for i, r_bin in enumerate(quantized_rhos):
                theta_bin = int(thetas[i] // BIN_SIZE) % N_ANGLE_BINS
                hist[r_bin - 1, theta_bin] += 1

        normalised_hist = hist / hist.sum()
        feature_vectors[j] = normalised_hist.flatten()

    return feature_vectors.flatten()