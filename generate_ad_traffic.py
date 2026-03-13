import helpers as hlp

def write_traffic(name, chiplet_ids):
    pairs = [(i, j) for i in chiplet_ids for j in chiplet_ids if i != j]
    prob = 1.0 / len(pairs)
    
    # Chiplet-level traffic: (scid, dcid)
    traffic_chiplet = {(i, j): prob for (i, j) in pairs}
    hlp.write_json(f"inputs/traffic_by_chiplet/traffic_{name}.json", traffic_chiplet)
        
    # Unit-level traffic: ((scid, suid), (dcid, duid))
    traffic_unit = {((i, 0), (j, 0)): prob for (i, j) in pairs}
    hlp.write_json(f"inputs/traffic_by_chiplet/traffic_{name}_unit.json", traffic_unit)

write_traffic("ad_dist", [0, 1, 2, 3])
write_traffic("ad_shared", [1, 2, 3, 4])
