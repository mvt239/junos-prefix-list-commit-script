"""
$ bb_fw_pl_update.py
 Updated: 06/18/25
 Updates prefix lists for direct neighbors with BB Prefixed int desc

 set system scripts commit allow-transients
 set system scripts commit file bb_fw_pl_update.py

 IPv4 prefix-list: PL-INET4-BB-DIRECT-NBRS
 IPv6 prefix-list: PL-INET6-BB-DIRECT-NBRS
"""

from junos import Junos_Configuration
import jcs
import ipaddress

def collect_prefixes():
    v4, v6 = set(), set()
    for iface in Junos_Configuration.findall("interfaces/interface"):
        # all int descs. Matches on BB prefix on all units and/or physical int
        ifdesc = iface.findtext("description", "")
        for unit in iface.findall("unit"):
            if ifdesc.startswith("BB") or unit.findtext("description", "").startswith("BB"):
                for addr in unit.findall("family/inet/address/name"):
                    try: v4.add(str(ipaddress.ip_network(addr.text.strip(), strict=False)))
                    except: pass
                for addr in unit.findall("family/inet6/address/name"):
                    try: v6.add(str(ipaddress.ip_network(addr.text.strip(), strict=False)))
                    except: pass
    return v4, v6

def current_prefixes(name):
    return {item.findtext("name").strip() for pl in Junos_Configuration.findall("policy-options/prefix-list")
            if pl.findtext("name") == name for item in pl.findall("prefix-list-item")}

def emit(pl_name, prefixes):
    entries = "".join(f"<prefix-list-item><name>{p}</name></prefix-list-item>" for p in sorted(prefixes))
    return f"<policy-options><prefix-list replace='replace'><name>{pl_name}</name>{entries}</prefix-list></policy-options>"

def main():
    new_v4, new_v6 = collect_prefixes()
    old_v4, old_v6 = current_prefixes("PL-INET4-BB-DIRECT-NBRS"), current_prefixes("PL-INET6-BB-DIRECT-NBRS")
    if new_v4 != old_v4: jcs.emit_change(emit("PL-INET4-BB-DIRECT-NBRS", new_v4), "transient-change", "xml")
    if new_v6 != old_v6: jcs.emit_change(emit("PL-INET6-BB-DIRECT-NBRS", new_v6), "transient-change", "xml")
    if new_v4 != old_v4 or new_v6 != old_v6:
        jcs.emit_warning(f"Commit script updated prefix-lists: PL-INET4-BB-DIRECT-NBRS={len(new_v4)}, PL-INET6-BB-DIRECT-NBRS={len(new_v6)}")

main()
