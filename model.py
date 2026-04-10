import numpy as np
from sklearn.linear_model import LogisticRegression

# Training data
# [study, attendance, ut_avg, ese]
X = np.array([
    [5, 90, 18, 55],
    [4, 80, 15, 50],
    [3, 70, 12, 45],
    [2, 60, 8, 30],
    [1, 50, 5, 20],
    [4, 85, 16, 52],
    [2, 55, 7, 28],
    [1, 40, 4, 15]
])

# Output: 1 = PASS, 0 = FAIL
y = np.array([1,1,1,0,0,1,0,0])

model = LogisticRegression()
model.fit(X, y)

def predict_result(study, att, ut, ese):
    data = np.array([[study, att, ut, ese]])
    return model.predict(data)[0]