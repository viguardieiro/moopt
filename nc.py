import numpy as np
import bisect
import copy
import logging
import time

from .mo_interface import bb_interface
from moopt.scalarization_interface import scalar_interface, single_interface
from .mo_utils import dominated, mo_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class nc(bb_interface,mo_metrics):
    def __init__(self, gap=0.1,  minsize=50, normalScalar = None, singleScalar = None, correction = 'sanchis'):
        self.__solutionsList = scalar_interface
        if not isinstance(normalScalar, scalar_interface) or \
            not isinstance(singleScalar, scalar_interface) or not isinstance(singleScalar, single_interface):
            raise ValueError('normalScalar'+' and '+'singleScalar'+'must be a mo_problem implementation.')

        self.__normalScalar = normalScalar
        self.__singleScalar = singleScalar
        self.__gap = gap
        self.__minsize = minsize
        self.__correction = correction

        self.__lowerBound = 0
        self.__upperBound = 1
        self.__solutionsList = []
        self.__candidatesList = []


    @property
    def gap(self): return self.__gap

    @property
    def minsize(self): return self.__minsize

    @property
    def upperBound(self): return self.__upperBound

    @property
    def lowerBound(self): return self.__lowerBound

    @property
    def solutionsList(self): return self.__solutionsList

    def __num_sol(self, steps, acc):
        if steps==[]:
            return 1
        else:
            csteps = copy.copy(steps)
            s = csteps.pop(0)
            sols = 0
            i=0
            while True:
               if acc+i*s<=1:
                   sols+=self.__num_sol(csteps,acc+i*s)
               else:
                   break
               i+=1
            return sols

    def __find_steps(self,max_sol):
        for m0 in range(2,max_sol+1):
            m =[int(m0*np.linalg.norm(self.__Ndir[i,:])/np.linalg.norm(self.__Ndir[0,:]))
                        for i in range(self.__M-1)]
            m = [mp if mp>1 else 2 for mp in m]
            steps = [1/(mp-1) for mp in m]
            n_sol = self.__num_sol(steps,0)
            if n_sol>=max_sol:
                break
        return m

    def __comb(self, mvec, comb=[]):
        if mvec==[]:
            bla = comb+[1-sum(comb)]
            return [bla]
        cmvec = copy.copy(mvec)
        m = cmvec.pop(0)
        delta = 1/(m-1)
        ncomb = []
        for i in range(m):
            auxcomb = comb+[delta*i]
            if sum(auxcomb)>1:
                break
            ncomb+=self.__comb(cmvec,auxcomb)
        return ncomb

    def inicialization(self,oArgs):
        """ Inicializate the objects of the scalarizations.
            Compute the solutions from the individual minima.
            Compute the global inferior bound and the global superior bound.
            Create the first region.

        Parameters
        ----------
        oArgs: tuple
            Arguents used by baseOpt

        Returns
        -------
        """
        self.__singleScalar.mo_ini(*oArgs)
        self.__normalScalar.mo_ini(*oArgs)

        self.__M = self.__singleScalar.M
        neigO=[]
        for i in range(self.__M):
            singleS = copy.copy(self.__singleScalar)
            singleS.mo_optimize(i,*oArgs)
            neigO.append(singleS.objs)
            self.__solutionsList.append(singleS)

        neigO=np.array(neigO)
        self.__globalL = neigO.min(0)
        self.__globalU = neigO.max(0)

        #self.__indivB = np.array(neigO)
        if self.__correction == 'sanchis':
            self.__normIndivB = np.ones((self.__M,self.__M))-np.eye(self.__M)
            Mu_ = self.__normIndivB
            Mu = (np.array(neigO)-self.__globalL).T
            self.__T = np.linalg.solve(Mu.T,Mu_.T).T
        else:
            self.__normIndivB = ((np.array(neigO)-self.__globalL)/(self.__globalU - self.__globalL)).T
            self.__T = np.diag(1/(self.__globalU - self.__globalL))
        self.__Ndir = self.__normIndivB[:,[-1]]-self.__normIndivB[:,:-1]
        mvec = self.__find_steps(self.__minsize)
        self.__combs = [np.array(c) for c in self.__comb(mvec)]



    def select(self):
        """ Selects the next regions to be optimized"""
        bounded_ = True
        while bounded_ and self.__candidatesList !=[]:
            candidate = self.__candidatesList.pop()
            bounded_ = dominated(candidate.l,self.solutionsList)
            if bounded_:
                self.__upperBound -= candidate.importance

        if bounded_:
            return None
        else:
            return candidate


    def update(self, solution):
        """ Update the variables

        Parameters
        ----------
        cand: box_scalar object
            A box scalarization object already optimized and feasible
        """
        if not dominated(solution.objs,self.solutionsList) and solution.feasible:
            self.__solutionsList.append(solution)


    def optimize(self, *oArgs):
        """Find a set of efficient solutions

        Parameters
        ----------
        oArgs: tuple
            Arguments used by baseOpt
        Returns
        -------
        """
        start = time.clock()
        self.inicialization(oArgs)

        for comb_ in self.__combs:
            X_ = self.__normIndivB @ comb_
            normalS = copy.copy(self.__normalScalar)
            normalS.mo_optimize(X_,self.__Ndir, self.__globalL, self.__T, *oArgs, solutionsList=self.__solutionsList)
            self.update(normalS)
        self.__fit_runtime = time.clock() - start