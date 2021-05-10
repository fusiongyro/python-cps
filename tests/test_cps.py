from cps.cps import CapabilityDefinition


def f_cps(resume):
    return 'executed'

def test_cps_single():
    CapabilityDefinition('f()').execute()