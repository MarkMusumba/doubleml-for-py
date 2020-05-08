import pytest
import math

from sklearn.base import clone
from sklearn.linear_model import LinearRegression

import doubleml.api as dml

from doubleml.tests.helper_general import get_n_datasets
from doubleml.tests.helper_pyvsr import export_smpl_split_to_r, r_MLPLR

from rpy2.robjects import pandas2ri
pandas2ri.activate()

# number of datasets per dgp
n_datasets = get_n_datasets()

@pytest.fixture(scope='module',
                params = range(n_datasets))
def idx(request):
    return request.param

@pytest.fixture(scope='module',
                params = ['IV-type', 'DML2018'])
def inf_model(request):
    return request.param


@pytest.fixture(scope='module',
                params = ['dml1', 'dml2'])
def dml_procedure(request):
    return request.param


@pytest.fixture(scope="module")
def dml_plr_pyvsr_fixture(generate_data1, idx, inf_model, dml_procedure):
    n_folds = 2
    n_rep_boot = 483

    # collect data
    data = generate_data1[idx]
    X_cols = data.columns[data.columns.str.startswith('X')].tolist()
    
    # Set machine learning methods for m & g
    learner = LinearRegression()
    ml_learners = {'ml_m': clone(learner),
                   'ml_g': clone(learner)}
    
    dml_plr_obj = dml.DoubleMLPLR(data, X_cols, 'y', ['d'],
                              ml_learners,
                              n_folds,
                              inf_model=inf_model,
                              dml_procedure=dml_procedure)

    #np.random.seed(3141)
    dml_plr_obj.fit()

    # fit the DML model in R
    all_train, all_test = export_smpl_split_to_r(dml_plr_obj.smpls[0])

    r_dataframe = pandas2ri.py2rpy(data)
    res_r = r_MLPLR(r_dataframe, inf_model, dml_procedure,
                    all_train, all_test)
    
    res_dict = {'coef_py': dml_plr_obj.coef,
                'coef_r': res_r[0],
                'se_py': dml_plr_obj.se,
                'se_r': res_r[1]}

    
    return res_dict


def test_dml_plr_pyvsr_coef(dml_plr_pyvsr_fixture):
    assert math.isclose(dml_plr_pyvsr_fixture['coef_py'],
                        dml_plr_pyvsr_fixture['coef_r'],
                        rel_tol=1e-9, abs_tol=1e-4)


def test_dml_plr_pyvsr_se(dml_plr_pyvsr_fixture):
    assert math.isclose(dml_plr_pyvsr_fixture['se_py'],
                        dml_plr_pyvsr_fixture['se_r'],
                        rel_tol=1e-9, abs_tol=1e-4)
