# utils.py
import numpy as np


def find_disconnected_regions(matrix):
    # Get the dimensions of the matrix
    rows, cols = matrix.shape

    # Initialize the label matrix with zeros
    label_matrix = np.zeros_like(matrix)

    # Define the connectivity (8-connectivity)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    # Helper function for Depth-First Search
    def dfs(r, c, current_label):
        stack = [(r, c)]
        label_matrix[r, c] = current_label
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
                    region_count[value] = set()
                region_count[value].add(label)

    # Find and return disconnected regions
    disconnected_regions = {
        value: len(labels) for value, labels in region_count.items() if len(labels) > 1
    }
    return disconnected_regions
