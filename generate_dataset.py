import pandas as pd
import random

data = []

for i in range(300):
    attendance = random.randint(40, 100)
    study_hours = round(random.uniform(0.5, 5), 1)
    internal_marks = random.randint(10, 50)
    assignment = random.randint(5, 20)
    previous_gpa = round(random.uniform(4, 9), 1)

    # Simple logic for result
    if attendance > 60 and internal_marks > 25:
        result = "Pass"
    else:
        result = "Fail"

    data.append([attendance, study_hours, internal_marks, assignment, previous_gpa, result])

df = pd.DataFrame(data, columns=[
    "Attendance", "StudyHours", "InternalMarks",
    "AssignmentScore", "PreviousGPA", "Result"
])

df.to_csv("dataset.csv", index=False)

print("Dataset generated successfully!")