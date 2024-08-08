# utils.py
import numpy as np


def find_disconnected_regions(matrix, pixelDead):
    # Get the dimensions of the matrix
    rows, cols = matrix.shape

    # Initialize the label matrix with zeros
    label_matrix = np.zeros_like(matrix)

    # Define the connectivity (8-connectivity)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    # Dictionary to store centroids of each label
    centroids = {}

    # Helper function for Depth-First Search
    def dfs(r, c, current_label):
        stack = [(r, c)]
        label_matrix[r, c] = current_label
        coordinates = [(r, c)]
        while stack:
            x, y = stack.pop()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < rows
                    and 0 <= ny < cols
                    and label_matrix[nx, ny] == 0
                    and matrix[nx, ny] == matrix[r, c]
                ):
                    label_matrix[nx, ny] = current_label
                    stack.append((nx, ny))
                    coordinates.append((nx, ny))

        # Calculate the centroid
        if coordinates:
            centroid_x = round(sum(x for x, y in coordinates) / len(coordinates))
            centroid_y = round(sum(y for x, y in coordinates) / len(coordinates))

            # Adjust centroid to ensure it lies within the region
            if (centroid_x, centroid_y) not in coordinates:
                closest_point = min(
                    coordinates,
                    key=lambda point: (point[0] - centroid_x) ** 2
                    + (point[1] - centroid_y) ** 2,
                )
                centroid_x, centroid_y = closest_point

            centroids[current_label] = (centroid_y, centroid_x)

    current_label = 1
    for r in range(rows):
        for c in range(cols):
            if matrix[r, c] != 0 and label_matrix[r, c] == 0:
                dfs(r, c, current_label)
                current_label += 1

    # Track the number of regions for each unique value
    region_count = {}
    for r in range(rows):
        for c in range(cols):
            if matrix[r, c] != 0:
                value = matrix[r, c]
                label = label_matrix[r, c]
                if value not in region_count:
                    region_count[value] = {}
                if label not in region_count[value]:
                    region_count[value][label] = centroids[label]

    # Find and return disconnected regions
    disconnected_regions = {
        value: {"count": len(labels), "centroids": list(labels.values())}
        for value, labels in region_count.items()
        if (len(labels) > 1) or (value in pixelDead)
    }
    return disconnected_regions
