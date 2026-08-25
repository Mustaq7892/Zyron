import inspect


class ToolRegistry:
    """Central registry for Zyron's dynamic capabilities."""

    def __init__(self):
        self._tools = {}

    def register(
        self,
        name,
        description,
        function,
        parameters=None,
        requires_confirmation=False,
    ):
        name = str(name).strip()
        if not name:
            raise ValueError("Tool name cannot be empty.")
        if not callable(function):
            raise TypeError(f"Tool '{name}' must have a callable function.")

        if parameters is None:
            parameters = self._infer_parameters(function)

        self._tools[name] = {
            "name": name,
            "description": str(description).strip(),
            "function": function,
            "parameters": parameters,
            "requires_confirmation": bool(requires_confirmation),
        }

    def _infer_parameters(self, function):
        parameters = {}
        signature = inspect.signature(function)

        for parameter_name, parameter in signature.parameters.items():
            if parameter_name in {"self", "cls"}:
                continue

            annotation = parameter.annotation
            if annotation is inspect.Parameter.empty:
                parameter_type = "string"
            elif annotation is str:
                parameter_type = "string"
            elif annotation is int:
                parameter_type = "integer"
            elif annotation is float:
                parameter_type = "number"
            elif annotation is bool:
                parameter_type = "boolean"
            else:
                parameter_type = "string"

            parameters[parameter_name] = {
                "type": parameter_type,
                "required": parameter.default is inspect.Parameter.empty,
            }

        return parameters

    def get(self, name):
        return self._tools.get(name)

    def get_names(self):
        return list(self._tools.keys())

    def get_all(self):
        return dict(self._tools)

    def get_descriptions(self):
        descriptions = {}
        for name, tool in self._tools.items():
            descriptions[name] = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
                "requires_confirmation": tool.get(
                    "requires_confirmation", False
                ),
            }
        return descriptions

    def execute(self, name, **arguments):
        tool = self.get(name)
        if tool is None:
            return {"success": False, "error": f"Unknown tool: {name}"}

        parameters = tool.get("parameters", {})
        for parameter_name, parameter_info in parameters.items():
            if (
                parameter_info.get("required", False)
                and parameter_name not in arguments
            ):
                return {
                    "success": False,
                    "error": (
                        f"Missing required argument '{parameter_name}' "
                        f"for tool '{name}'."
                    ),
                }

        unknown_arguments = [
            argument for argument in arguments if argument not in parameters
        ]
        if unknown_arguments:
            return {
                "success": False,
                "error": (
                    f"Unknown argument(s) for tool '{name}': "
                    f"{', '.join(unknown_arguments)}"
                ),
            }

        try:
            result = tool["function"](**arguments)
            return {"success": True, "result": result}
        except Exception as error:
            return {"success": False, "error": str(error)}