from typing import Any, Dict


class BaseAppException(Exception):
    def __init__(self, error_class: Any, *args: Any, **kwargs: Any):
        self.error_class = error_class
        self.args_data = args
        self.kwargs_data = kwargs
        super().__init__(str(error_class.get_status(error_class, *args, **kwargs)))

    def get_status(self) -> Dict[str, Any]:
        return self.error_class.get_status(self.error_class, *self.args_data, **self.kwargs_data)
