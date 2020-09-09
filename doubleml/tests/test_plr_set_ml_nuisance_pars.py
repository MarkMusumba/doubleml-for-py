import numpy as np
import pytest
import math

from sklearn.base import clone
from sklearn.linear_model import Lasso

import doubleml as dml

from doubleml.tests.helper_general import get_n_datasets


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
def dml_plr_fixture(generate_data1, idx, inf_model, dml_procedure):
    boot_methods = ['normal']
    n_folds = 2
    n_rep_boot = 502

    # collect data
    data = generate_data1[idx]
    X_cols = data.columns[data.columns.str.startswith('X')].tolist()

    alpha = 0.05
    learner = Lasso(alpha=alpha)
    # Set machine learning methods for m & g
    ml_learners = {'ml_m': clone(learner),
                   'ml_g': clone(learner)}

    np.random.seed(3141)
    obj_dml_data = dml.DoubleMLData(data, 'y', ['d'])
    dml_plr_obj = dml.DoubleMLPLR(obj_dml_data,
                                  ml_learners,
                                  n_folds,
                                  inf_model=inf_model,
                                  dml_procedure=dml_procedure)

    dml_plr_obj.fit()

    np.random.seed(3141)
    learner = Lasso()
    # Set machine learning methods for m & g
    ml_learners = {'ml_m': clone(learner),
                   'ml_g': clone(learner)}

    dml_plr_obj_ext_set_par = dml.DoubleMLPLR(obj_dml_data,
                                              ml_learners,
                                              n_folds,
                                              inf_model=inf_model,
                                              dml_procedure=dml_procedure)
    dml_plr_obj_ext_set_par.set_ml_nuisance_params({'g_params': {'alpha': alpha},
                                                    'm_params': {'alpha': alpha}})
    dml_plr_obj_ext_set_par.fit()

    
    res_dict = {'coef': dml_plr_obj.coef,
                'coef_manual': dml_plr_obj_ext_set_par.coef,
                'se': dml_plr_obj.se,
                'se_manual': dml_plr_obj_ext_set_par.se,
                'boot_methods': boot_methods}
    
    for bootstrap in boot_methods:
        np.random.seed(314122)
        dml_plr_obj.bootstrap(method = bootstrap, n_rep=n_rep_boot)
        res_dict['boot_coef' + bootstrap] = dml_plr_obj.boot_coef
        
        np.random.seed(314122)
        dml_plr_obj_ext_set_par.bootstrap(method = bootstrap, n_rep=n_rep_boot)
        res_dict['boot_coef' + bootstrap + '_manual'] = dml_plr_obj_ext_set_par.boot_coef
    
    return res_dict


@pytest.mark.filterwarnings("ignore:Using the same")
def test_dml_plr_coef(dml_plr_fixture):
    assert math.isclose(dml_plr_fixture['coef'],
                        dml_plr_fixture['coef_manual'],
                        rel_tol=1e-9, abs_tol=1e-4)


@pytest.mark.filterwarnings("ignore:Using the same")
def test_dml_plr_se(dml_plr_fixture):
    assert math.isclose(dml_plr_fixture['se'],
                        dml_plr_fixture['se_manual'],
                        rel_tol=1e-9, abs_tol=1e-4)


@pytest.mark.filterwarnings("ignore:Using the same")
def test_dml_plr_boot(dml_plr_fixture):
    for bootstrap in dml_plr_fixture['boot_methods']:
        assert np.allclose(dml_plr_fixture['boot_coef' + bootstrap],
                           dml_plr_fixture['boot_coef' + bootstrap + '_manual'],
                           rtol=1e-9, atol=1e-4)
