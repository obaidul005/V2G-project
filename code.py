# V2G-project
 Electric Vehicle Charging Simulation

 import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import networkx as nx
import time

# Initialize the Dash app
app = dash.Dash(__name__)

# Define electric car models
electric_car_models = ["Nissan Leaf", "Ford F-150 Lighting", "Nissan e-NV 200", "Kia EV6", "Tesla Model S"]

# Define grid options for different regulatory frameworks
regulatory_frameworks = {
    "EU": ["Option 1", "Option 2", "Option 3"],
    "Asian": ["Option A", "Option B", "Option C"],
    "UK": ["Option X", "Option Y", "Option Z"],
    "USA": ["Option I", "Option II", "Option III"]
}

# Define charger types
charger_types = ["Level-1", "Level-2", "CCS", "Level-3"]

# Define initial values
initial_state = {
    "regulation-dropdown": None,
    "action-dropdown": None,
    "charger-dropdown": None,
    "car-dropdown": None
}

# Define compatibility dictionary for charger types and regulatory frameworks
compatibility = {
    "Level-1": ["Asian", "EU", "UK", "USA"],
    "Level-2": ["Asian", "EU", "UK", "USA"],
    "CCS": ["Asian", "EU", "UK", "USA"],
    "Level-3": {"Charging": {"Tesla Model S"}, "Discharging": set()}
}

# Create a directed graph
G = nx.DiGraph()

# Add nodes for grid, charging station, charger, car, regulation, and charger type
G.add_node("Grid", pos=(0, 3), symbol="⚡️")
G.add_node("Charging Station", pos=(3, 3), symbol="🔌")
G.add_node("Car", pos=(7, 3), symbol="🚗🔋")

# Add edges to represent power flow
G.add_edge("Grid", "Charging Station")
G.add_edge("Charging Station", "Car")


# Define Dash app layout
app.layout = html.Div([
    html.H1("Electric Vehicle Charging Simulation"),
    html.Div([
        html.Label("Select Regulatory Framework:"),
        dcc.Dropdown(
            id="regulation-dropdown",
            options=[{"label": "", "value": ""}],
            value=initial_state["regulation-dropdown"]
        ),
        html.Label("Select Action:"),
        dcc.Dropdown(
            id="action-dropdown",
            options=[{"label": "", "value": ""}],
            value=initial_state["action-dropdown"]
        ),
        html.Label("Select Charger Type:"),
        dcc.Dropdown(
            id="charger-dropdown",
            options=[{"label": "", "value": ""}],
            value=initial_state["charger-dropdown"]
        ),
        html.Label("Select Car Model:"),
        dcc.Dropdown(
            id="car-dropdown",
            options=[{"label": "", "value": ""}],
            value=initial_state["car-dropdown"]
        ),
        html.Div(id="discharge-slider-container"),
        html.Button("Reset", id="reset-button", n_clicks=0)
    ]),
    dcc.Graph(id="flowchart", config={'displayModeBar': False})
])

# Define callback to update dropdown options based on user selections
@app.callback(
    Output("discharge-slider-container", "children"),
    [Input("action-dropdown", "value")]
)
def update_slider(action):
    if action == "Discharging":
        return html.Div([
            html.Label("Select Discharge Percentage:"),
            dcc.Slider(
                id="discharge-slider",
                min=0,
                max=100,
                step=1,
                value=50,
                marks={i: f"{i}%" for i in range(0, 101, 10)}
            )
        ])
    else:
        return None

# Define callback to update dropdown options based on user selections
@app.callback(
    [Output("regulation-dropdown", "options"),
     Output("action-dropdown", "options"),
     Output("charger-dropdown", "options"),
     Output("car-dropdown", "options")],
    [Input("regulation-dropdown", "value"),
     Input("action-dropdown", "value"),
     Input("charger-dropdown", "value"),
     Input("car-dropdown", "value")]

)
def update_dropdown_options(selected_regulation, selected_action, selected_charger, selected_car_model):
    regulation_options = [{"label": framework, "value": framework} for framework in regulatory_frameworks.keys()]
    action_options = [{"label": "Charging", "value": "Charging"}, {"label": "Discharging", "value": "Discharging"}]
    charger_options = [{"label": charger_type, "value": charger_type} for charger_type in charger_types if charger_type != "Charger Type"]
    car_options = [{"label": model, "value": model} for model in electric_car_models]
    return regulation_options, action_options, charger_options, car_options

# Define callback to update the flowchart based on user inputs
@app.callback(
    Output("flowchart", "figure"),
    [Input("regulation-dropdown", "value"),
     Input("action-dropdown", "value"),
     Input("charger-dropdown", "value"),
     Input("car-dropdown", "value")]
)
def update_flowchart(selected_regulation, selected_action, selected_charger, selected_car_model):
    # Create Plotly figure
    fig = go.Figure()

    # Add nodes and edges to the figure
    for node, (x, y) in nx.get_node_attributes(G, "pos").items():
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text", text=[f"{node} {G.nodes[node]['symbol']}"],
            textposition="top center", marker=dict(size=30, color="black")
        ))

    # Add rectangle surrounding the graph
    x_values = [nx.get_node_attributes(G, "pos")[node][0] for node in ["Grid", "Charging Station", "Car"]]
    y_values = [nx.get_node_attributes(G, "pos")[node][1] for node in ["Grid", "Charging Station", "Car"]]
    x_min = min(x_values) - 1
    x_max = max(x_values) + 1
    y_min = min(y_values) - 1
    y_max = max(y_values) + 1

    # Set initial border color of the rectangle to black
    border_color = "black"

    if selected_charger and selected_action:
        if selected_action == "Charging":
            if selected_charger == "Level-3":
                if selected_car_model in ["Nissan Leaf", "Kia EV6"]:
                    # Set border color to red if not compatible
                    border_color = "red"
                else:
                    # Set border color to green if compatible
                    border_color = "green"
            else:
                # Set border color to green for other charger types
                border_color = "green"
        elif selected_action == "Discharging":
            if selected_car_model == "Tesla Model S":
                # Set border color to red if not compatible for Tesla
                border_color = "red"
            else:
                # Set border color to red for other car models
                border_color = "green"

    fig.add_shape(
        type="rect",
        x0=x_min,
        y0=y_min,
        x1=x_max,
        y1=y_max,
        line=dict(color=border_color, width=2),
        fillcolor="rgba(0,0,0,0)"
    )

    # Initialize text annotations
    annotation_text = None
    hover_text = None

    if selected_charger and selected_regulation and selected_car_model:
        # Check compatibility
        if selected_action == "Charging":
            if selected_charger == "Level-3":
                if selected_car_model in ["Nissan Leaf", "Kia EV6"]:
                    # Set border color to red if not compatible
                    border_color = "red"
                    annotation_text = "Charger type doesn't compatible with car"
                else:
                    # Set border color to green if compatible
                    border_color = "green"
            else:
                # Set border color to green for other charger types
                border_color = "green"
        elif selected_action == "Discharging":
            if selected_charger == "Level-3":
                # Set border color to red if not compatible
                border_color = "red"
                if selected_car_model == "Tesla Model S":
                    annotation_text = "Tesla not compatible with discharging action"
                else:
                    annotation_text = "Discharging action not supported with this charger type"
            else:
                # Set border color to red for other charger types
                border_color = "green"

    # Add text annotation
    if annotation_text:
        fig.add_annotation(
            x=(x_min + x_max) / 2,
            y=y_max + 0.5,
            text=annotation_text,
            showarrow=False,
            font=dict(color="red", size=14),
            bgcolor="white",
            bordercolor="red",
            borderwidth=1,
            borderpad=4,
            opacity=0.8
        )

    # Draw lines dynamically based on user selections

    if selected_action:
        fig.add_trace(go.Scatter(
            x=[nx.get_node_attributes(G, "pos")["Grid"][0], nx.get_node_attributes(G, "pos")["Charging Station"][0]],
            y=[nx.get_node_attributes(G, "pos")["Grid"][1], nx.get_node_attributes(G, "pos")["Charging Station"][1]],
            mode="lines",
            line=dict(color="green" )
        ))
        if selected_charger and selected_regulation:
            if selected_action == "Charging":
                if selected_charger == "Level-3":
                    if selected_car_model != "Tesla Model S":
                        # Draw line in red between Grid to Car
                        fig.add_trace(go.Scatter(
                            x=[nx.get_node_attributes(G, "pos")["Grid"][0], nx.get_node_attributes(G, "pos")["Charging Station"][0]],
                            y=[nx.get_node_attributes(G, "pos")["Grid"][1], nx.get_node_attributes(G, "pos")["Charging Station"][1]],
                            mode="lines",
                            line=dict(color="green", width=3)
                        ))
            elif selected_action == "Discharging":
                if selected_charger == "Level-3":
                    # Draw line in red between Grid to Car
                    fig.add_trace(go.Scatter(
                        x=[nx.get_node_attributes(G, "pos")["Grid"][0], nx.get_node_attributes(G, "pos")["Charging Station"][0]],
                        y=[nx.get_node_attributes(G, "pos")["Grid"][1], nx.get_node_attributes(G, "pos")["Charging Station"][1]],
                        mode="lines",
                        line=dict(color="red", width=3)
                    ))


    if selected_car_model:
        fig.add_trace(go.Scatter(
            x=[nx.get_node_attributes(G, "pos")["Charging Station"][0], nx.get_node_attributes(G, "pos")["Car"][0]],
            y=[nx.get_node_attributes(G, "pos")["Charging Station"][1], nx.get_node_attributes(G, "pos")["Car"][1]],
            mode="lines",
            line=dict(color="red" if border_color == "red" else "green", width=3)
        ))

    # Update layout
    fig.update_layout(title="Electric Vehicle Charging Simulation", xaxis=dict(range=[x_min-1, x_max+1], showticklabels=False),
                      yaxis=dict(range=[y_min-1, y_max+1], showticklabels=False), showlegend=False)

    return fig

# Define callback to reset dropdowns
@app.callback(
    [Output("regulation-dropdown", "value"),
     Output("action-dropdown", "value"),
     Output("charger-dropdown", "value"),
     Output("car-dropdown", "value")],
    [Input("reset-button", "n_clicks")],
    [State("regulation-dropdown", "options"),
     State("action-dropdown", "options"),
     State("charger-dropdown", "options"),
     State("car-dropdown", "options")]
)
def reset_dropdown(n_clicks, regulation_options, action_options, charger_options, car_options):
    if n_clicks > 0:
        return None, None, None, None
    else:
        raise dash.exceptions.PreventUpdate


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
