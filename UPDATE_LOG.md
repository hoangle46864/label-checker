# Update Log for Image Segmentation QA Tool

---

## Initial Script

- **Date**: 30-05-2024
- **Changes**:
  - Basic functionalities to load images and masks.
  - Basic GUI components such as buttons, progress bars, and labels.
  - Methods for navigating objects and marking them as "Yes" or "No".
  - Basic object state management.

---

## Separation into Multiple Modules

- **Date**: 12-06-2024
- **Modules Created**:
  - `custom_graphics_view.py`
  - `image_viewer.py`
  - `worker.py`

### `custom_graphics_view.py`

- **Changes**:
  - Created `CustomGraphicsView` class.
  - Implemented mouse events for zooming and object selection.
  - Added `drawBoundingBox` method to draw bounding boxes around objects.

### `image_viewer.py`

- **Changes**:
  - Main application logic moved to `ImageViewer` class.
  - Integrated `CustomGraphicsView`.
  - Added methods for loading and saving progress (`loadInfo`, `saveInfo`).
  - Added methods for marking objects (`markObjectYes`, `markObjectNo`).
  - Added `getReason` method to prompt for rejection reason with pre-filled coordinates.

### `worker.py`

- **Changes**:
  - Created `Worker` class to handle background processing.
  - Added signals for progress updates and completion.

---

## Enhancements and Bug Fixes

- **Date**: 12-06-2024
- **Changes**:
  - Updated `loadInfo` and `saveInfo` methods to use "Object Number" instead of "Number object".
  - Formatted "Object Number" as `label_{object_number}` in CSV files.
  - Added bounding box drawing in `nextObject` and `previousObject` methods.
  - Improved `getReason` method to pre-fill coordinates and move cursor to the end.
  - Added handling for user cancel actions in `loadImage` method.
  - Ensured no operations are performed if user cancels file selection.
  - Refined error handling in `loadImage` method.

---

## Further Enhancements

- **Date**: 19-06-2024
- **Changes**:
  - Added double-click event to select objects in `CustomGraphicsView`.
  - Implemented method to update object list selection and trigger mask change.
  - Improved user experience by ensuring coordinates are included in rejection reasons.

---

## Add multi channel views

- **Date**: 06-07-2024
- **Changes**:
  - Added support for multi-channel views.

## Future Updates

- **Plan**:
  - Optimize image loading and processing time.
  - Enhance UI with additional features like object filtering and search.
  - Implement more robust error handling and logging.
  - Add unit tests for individual modules.

---
