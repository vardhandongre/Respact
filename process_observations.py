def process_ob(ob):
    '''
    Process the observation to remove the initial location information.
    ob: str
    '''
    if ob.startswith('You arrive at loc '):
        ob = ob[ob.find('. ')+2:]    
    return ob