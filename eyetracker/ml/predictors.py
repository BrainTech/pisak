
import numpy as np

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.cross_decomposition import PLSRegression

# http://stats.stackexchange.com/questions/4517/regression-with-multiple-dependent-variables

class PolynomialPredictor:
    def __init__(self):
        self._create_poly(2)
        self.linear_regression_x = \
            LinearRegression(fit_intercept=True,
                             normalize=False,
                             copy_X=True,
                             n_jobs=-1)
        self.linear_regression_y = \
            LinearRegression(fit_intercept=True,
                             normalize=False,
                             copy_X=True,
                             n_jobs=-1)

    def predict(self, values):
        values_poly = self.polynomial_features.fit_transform(values)
        # print(values_poly)

        predicted_x = self.linear_regression_x.predict(values_poly)
        predicted_y = self.linear_regression_y.predict(values_poly)
        # print(predicted_x, predicted_y)

        return predicted_x[0], predicted_y[0]

    def train(self, measured_values, screen_points, degree=2):
        assert measured_values.shape[0] == screen_points.shape[0]
        # print('measured_values:\n{}'.format(measured_values))
        # print('screen_points:\n{}'.format(screen_points))

        self._create_poly(degree)

        screen_points_x = screen_points[:, 0]
        screen_points_y = screen_points[:, 1]

        measured_values_poly = self.polynomial_features.fit_transform(measured_values)

        self.linear_regression_x.fit(measured_values_poly, screen_points_x)
        self.linear_regression_y.fit(measured_values_poly, screen_points_y)

    def save(self, file_name):
        degree = self.polynomial_features.degree
        coef_x = self.linear_regression_x.coef_
        coef_y = self.linear_regression_y.coef_
        data = {
            'degree': degree,
            'coef_x': coef_x,
            'coef_y': coef_y
        }
        # TODO: save data to file (in json)

    def load(self, file_name):
        pass

    def _create_poly(self, degree):
        self.polynomial_features = \
            PolynomialFeatures(degree=degree,
                               interaction_only=False,
                               include_bias=True)


class PLSPredictor:
    def __init__(self):
        self.pls2 = PLSRegression(n_components=2,
                                  scale=True,
                                  max_iter=500,
                                  tol=1e-06,
                                  copy=True)

    def predict(self, values):
        self.pls2.predict(values)

    def train(self, measured_values, screen_points):
        self.pls2.fit(measured_values, screen_points)


if __name__ == '__main__':
    measured_values = np.array([[0, 0, 0.5, 2],
                                [0, 1, 0.5, 2],
                                [1, 0, 0.5, 2],
                                [1, 1, 0.5, 2]])

    screen_points = np.array([[0, 0],
                              [0, 1],
                              [1, 0],
                              [1, 1]])

    prediction_point = np.array([0.5, 0.5, 0.5, 0.5])

    poly_predictor = PolynomialPredictor()
    poly_predictor.train(measured_values, screen_points, degree=2)
    poly_prediction = poly_predictor.predict(prediction_point)
    print(poly_prediction)

    pls_predictor = PLSPredictor()
    pls_predictor.train(measured_values, screen_points)
    pls_prediction = pls_predictor.predict(prediction_point)
    print(pls_prediction)
