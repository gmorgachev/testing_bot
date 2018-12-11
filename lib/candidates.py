import sys

sys.path.insert(0, "../CSharpCodeChecker/")
from NNCA.lib.model import Model
from NNCA.lib.data_extraction import Data


class TestingBase:
    params = {}

    def __init__(self):
        return

    def run(self, logger):
        raise NotImplementedError()


class TestingNNCA(TestingBase):
    params = {
        "num_edge_types": 8,
        "batch_size": 5,
        "learning_rate": 10,
        "prop_step": 6,
        "dropout_prob": 0.5,
        "fit_encoders": False,
        "max_nodes": 12000,
        "optimizer": "adadelta",
        "lr_step_size": 10,
        "lr_gamma": 0.5,
        "categorical_kind": False,
        "batch_normalization": True,
        "loss_function": "ce",
        "train_size": 101,
        "valid_size": 10,
        "valid_step": 50,
        "data_project": "lucene"
    }

    def __init__(self):
        TestingBase.__init__(self)
        self.args = TestingNNCA.params

    def run(self, logger):
        assert self.args["data_project"] in ["lucene", "cassandra"], "data error"
        if self.args["data_project"] is "cassandra":
            logger.warning("cassandra")
            data = Data(raw_data_dir=r"C:/workspace/CSharpCodeChecker/NNCA/raw_data/Cassandra/")
        else:
            logger.warning(self.args["data_project"])
            data = Data(raw_data_dir=r"C:/workspace/CSharpCodeChecker/NNCA/raw_data/Lucene/")
        
        model = Model(params=self.args, data=data, logger=logger)
        valid_it = model.train_model(self.args["train_size"], self.args["valid_step"], self.args["valid_size"], debug=True, log=True)
