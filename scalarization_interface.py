# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class scalar_interface(metaclass=ABCMeta):
    ## - propertys
    @property
    @abstractmethod
    def M(self):
        pass

    @property
    @abstractmethod
    def feasible(self):
        pass

    @property
    @abstractmethod
    def optimum(self):
        pass

    @property
    @abstractmethod
    def objs(self):
        pass
    
    @property
    @abstractmethod
    def x(self):
        pass
        
    @abstractmethod
    def optimize(self, *args):
        """Calculates the a multiobjective scalarization"""
        pass

    '''
    def optimize(self, *args):
        self.mo_optimize(*args)
        if not (hasattr(self, 'optMessage') and hasattr(self, 'feasible') and hasattr(self, 'optimum') and hasattr(self, 'objs')):
            raise ValueError("The mo_optimize implementation must set optMessage and optStatus and feasible and optimum and objs attributes")
    '''

class w_interface(metaclass=ABCMeta):
    ## - propertys
    @property
    @abstractmethod
    def w(self):
        pass
    
class single_interface(metaclass=ABCMeta):
    ## - propertys
    @property
    @abstractmethod
    def w(self):
        pass