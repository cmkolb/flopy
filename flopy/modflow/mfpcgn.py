from flopy.mbase import Package

class ModflowPcgn(Package):
    '''Pcgn Package
    Only programmed to work with the default values; may need work for other options'''
    def __init__(self, model, iter_mo=50, iter_mi=30, close_h=1e-5, close_r=1e-5, \
                 relax=1.0, ifill=0, unit_pc=0, unit_ts=0, \
                 adamp=0, damp=1.0, damp_lb=0.001, rate_d=0.1, chglimit=0., \
                 acnvg=0, cnvg_lb=0.001, mcnvg=2, rate_c=-1.0, ipunit=0, \
                 extension=['pcgn'], unit_number=27):
        name = ['PCGN']
        units = [unit_number]
        extra = ['']
        tu = (unit_pc,unit_ts,ipunit)
        ea = ('pcgni','pcgnt','pcgno')
        for [t,e] in zip(tu,ea):
            if t > 0:
                extension.append( e )
                name.append( 'DATA' )
                units.append( t )
                extra.append( 'REPLACE' )
        Package.__init__(self, model, extension=extension, name=name, unit_number=units, extra=extra) # Call ancestor's init to set self.parent, extension, name and unit number
        self.heading = '# PCGN for MODFLOW, generated by Flopy.'
        self.url = 'pcgn.htm'
        self.iter_mo = iter_mo
        self.iter_mi = iter_mi
        self.close_h = close_h
        self.close_r = close_r
        self.relax = relax
        self.ifill = ifill
        self.unit_pc = unit_pc
        self.unit_ts = unit_ts
        self.adamp = adamp
        self.damp = damp
        self.damp_lb = damp_lb
        self.rate_d = rate_d
        self.chglimit = chglimit
        self.acnvg = acnvg
        self.cnvg_lb = cnvg_lb
        self.mcnvg = mcnvg
        self.rate_c = rate_c
        self.ipunit = ipunit
        #--error trapping
        if self.ifill < 0 or self.ifill > 1:
            raise TypeError,\
              'PCGN: ifill must be 0 or 1 - an ifill value of {0} was specified'.format( self.ifill )
        #--add package
        self.parent.add_package(self)

    def __repr__( self ):
        return 'Preconditioned conjugate gradient solver with improved nonlinear control package class'
    def write_file(self):
        # Open file for writing
        f_pcgn = open(self.fn_path, 'w')
        f_pcgn.write( '{0:s}\n'.format(self.heading) )
        f_pcgn.write( ' {0:9d} {1:9d} {2:9.3g} {3:9.3g}\n'.format( self.iter_mo,self.iter_mi,self.close_r,self.close_h ) )
        f_pcgn.write( ' {0:9.3g} {1:9d} {2:9d} {3:9d}\n'.format( self.relax,self.ifill,self.unit_pc,self.unit_ts ) )
        f_pcgn.write( ' {0:9d} {1:9.3g} {2:9.3g} {3:9.3g} {4:9.3g}\n'.format( self.adamp, self.damp, self.damp_lb, self.rate_d, self.chglimit ) )
        f_pcgn.write( ' {0:9d} {1:9.3g} {2:9d} {3:9.3g} {4:9d}\n'.format( self.acnvg, self.cnvg_lb, self.mcnvg, self.rate_c, self.ipunit ) )
        f_pcgn.close()
