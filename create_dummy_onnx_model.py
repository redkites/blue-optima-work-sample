import onnx
from onnx import helper
from onnx import TensorProto
import argparse

"""
Allows for the regeneration of the onnx model if needed.
The size of the onnx model generated is controlled by the size parameter, defaulting to 100.

Running:
    ```
    python create_dummy_onnx_model.py --size {size of the model}
    ```
"""

def create_dummy_onnx_model(output_path: str = 'app/model.onnx', size: int = 1):
    """
    Creates a dummy ONNX model that takes a single float as input and
    outputs a single float (composed of 'size' identity operations).

    Args:
        output_path (str): The path to save the ONNX model.
        size (int): The number of sequential identity operations in the model.
                    This can be considered a proxy for the model's "size"
                    in terms of processing steps.
    """

    # Define graph input
    input_name = 'input'
    input_value_info = helper.make_tensor_value_info(
        input_name, TensorProto.FLOAT, [1, 1]
    )

    # Define graph output
    output_name = 'output'
    output_value_info = helper.make_tensor_value_info(
        output_name, TensorProto.FLOAT, [1, 1]
    )

    # Create a list to hold the nodes
    nodes = list()
    current_input_name = input_name
    for i in range(size):
        node_name = f'identity_{i}'
        current_output_name = f'intermediate_output_{i}' if i < size - 1 else output_name
        node_def = helper.make_node(
            'Identity',
            [current_input_name],
            [current_output_name],
            name=node_name
        )
        nodes.append(node_def)
        current_input_name = current_output_name

    # Create the graph
    graph_def = helper.make_graph(
        nodes,
        'dummy-model-graph',
        [input_value_info],
        [output_value_info],
    )

    # Create the model
    model_def = helper.make_model(graph_def, producer_name='dummy-onnx-model-creator', opset_imports=[helper.make_opsetid("", 20)])

    # Save the ONNX model
    onnx.save(model_def, output_path)

    print(f"Dummy ONNX model created with size {size} and saved to: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a dummy ONNX model with a specified size.')
    parser.add_argument('--size', type=int, default=1, help='The number of sequential identity operations in the model.')
    parser.add_argument('--output_path', type=str, default='app/model.onnx', help='The path to save the ONNX model.')

    args = parser.parse_args()

    create_dummy_onnx_model(output_path=args.output_path, size=args.size)
    print("\nTo use this model, ensure it's in the 'app/' directory of your project.")
