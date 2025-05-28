import gurobipy
from gurobipy import Model, GRB, tuplelist

m = Model("Pipeline_Network")

nodes = list(range(14))
#0 = A1 , #1 = B1, #2 = C1 , #3 = F1 , #4 = blank1 , #5 = blank2 , #6 = blank3 , #7 = blank4
#8 = A2 , #9 = blank5 , #10 = blank6 , #11 = F2 , #12 = B2 , #13 = C2
arcs = [(1, 0), (0, 4), (4, 3), (3, 9), (12, 9), (9, 10), (4, 10), (10, 13), (10, 11),
        (5, 4), (6, 5), (7, 6), (8, 7), (11, 7), (5, 11), (6, 2)]
arcs = tuplelist(arcs)

# Decision variables for the flow of each commodity through each arc
commodities = ['a', 'b', 'x', 'y']
flow = m.addVars(arcs, commodities, name="flow")

# Constraints
for arc in arcs:
    for commodity in commodities:
        m.addConstr(flow[arc[0], arc[1], commodity] >= 0)       # non-negativity constraint
    m.addConstr(gurobipy.quicksum(flow[arc[0], arc[1], commodity] for commodity in commodities) <= 10)     # total arc flow <= 10

# Node Constraints
for node in nodes:
    for commodity in commodities:
        inflow = gurobipy.quicksum(flow[i, j, commodity] for i, j in arcs.select('*', node))
        outflow = gurobipy.quicksum(flow[i, j, commodity] for i, j in arcs.select(node, '*'))
        
        if node in [0,8]:
            if commodity == 'a':
                m.addConstr(outflow >= inflow)      # only A nodes can produce commodity a
        if node in [1,12]:
            if commodity == 'b':
                m.addConstr(outflow >= inflow)      # only B nodes can produce commodity b
        #else:
         #   for i, j in arcs.select(node,'*'):
          #      m.addConstr(flow[i, j, commodity] == 0)     # nodes cannot produce x or y commodities
        
        if node in [3,11]:
            # F nodes conversion equations for commodities x and y
            for i, j in arcs.select(node, '*'):
                m.addConstr(flow[i, j, 'x'] <= 2 * flow[i, j, 'a'] + flow[i, j, 'b'])
                m.addConstr(flow[i, j, 'y'] <= flow[i, j, 'a'] + 3 * flow[i, j, 'b'])
                #m.addConstr(inflow == flow[i, j, 'x'] + flow[i, j, 'y'])

        elif node in [2,13]:
            for i, j in arcs.select('*',node):
                m.addConstr(flow[i, j, 'a'] == 0)
                m.addConstr(flow[i, j, 'b'] == 0)
                # C nodes cannot receive a or b

        else:
            # allows blank nodes to only pass on commodities from incoming arcs
            m.addConstr(inflow == outflow)

# Objective Function
m.setObjective(gurobipy.quicksum(2 * flow[i, j, 'x'] + 3 * flow[i, j, 'y'] for i, j in arcs.select('*', 2)) +
    gurobipy.quicksum(2 * flow[i, j, 'x'] + 3 * flow[i, j, 'y'] for i, j in arcs.select('*', 13)), GRB.MAXIMIZE)

m.optimize()

output_file_path = "solution.txt"

if m.status == GRB.OPTIMAL:
    print("Optimal flow:")
    with open(output_file_path, "w") as file:
        for arc in arcs:
            for commodity in commodities:
                if flow[arc[0], arc[1], commodity].x != 0:
                    line = f"{flow[arc[0], arc[1], commodity].varName}: {flow[arc[0], arc[1], commodity].x}\n"
                    print(line)
                    file.write(line)

        total_revenue_line = f"Total Revenue: {m.objVal}\n"
        print(total_revenue_line)
        file.write(total_revenue_line)

    print(f"Solution saved to {output_file_path}")
else:
    print("No solution")
