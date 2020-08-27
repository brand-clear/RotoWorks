# RotoWorks

### Overview
RotoWorks is a desktop application that guides users through as-received inspections of used mechanical systems. 

### Dependencies
Users should have Innovmetric's PolyWorks Inspector and Autodesk's AutoCAD installed on their local machine. Additionally, a portable CMM device (e.g. Faro Arm) is required to collect the measurements.

### Inspection
Each feature is recorded twice with a portable CMM device. RotoWorks will apply its own internal metrics for measurement validation. If a feature is deemed invalid, the user is prompted with an explanation and may choose to remeasure or cancel the operation.

### Documentation
After all dimensional data is collected and exported, the user may auto-populate the inspection results in AutoCAD as long as an approved DWG file is open.
