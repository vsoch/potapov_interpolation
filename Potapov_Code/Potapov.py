# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 13:59:30 2015

@author: Gil Tabak
@title: Potapov

The code in this file implements the procedure for finding Blaschke-Potapov
products to approximate given functions near poles.

Please see section 6.2 in our manuscript for details: http://arxiv.org/abs/1510.08942
(to be published in EPJ QT).

"""

import numpy as np
import functions as f
import matplotlib.pyplot as plt
import numpy.linalg as la


def plot(L,dx,func,(i,j),*args):
    '''A nice function for plotting components of matrix-valued functions.

    Args:
        L (float): length along which to plot

        dx (float): step length to take

        func (function): complex matrix-valued function

        i,j (tuple of ints): coordinate to plot

        args (functions): Desired transformations on the inputs

    '''
    x = np.linspace(-L,L,2.*L/dx)
    for arg in args:
        plt.plot(x,[func(arg(x_el*1j)[i,j]) for x_el in x ])
    return

def Potapov_prod(z,poles,vecs,N):
    r'''

    Takes a transfer function T(z) that outputs numpy matrices for imaginary
    :math:`z = i \omega` and the desired poles that characterize the modes.
    Returns the Potapov product as a function approximating the original
    transfer function.

    Args:
        z (complex number): value where product is evaluated

        poles(list of complex numbers): The poles of the Potapov product.

        vecs (list of complex-valued matrices): The eigenvectors corresponding to
        the orthogonal projectors of the Potapov product.

        N (int): Dimensionality of the the range.

    Returns:
        Complex-valued matrix of size :math:`N \times N`.

    '''
    R = np.asmatrix(np.eye(N))
    for pole_i,vec in zip(poles,vecs):
        Pi = vec*vec.H
        R = R*(np.eye(N) - Pi + Pi * ( z + pole_i.conjugate() )/( z - pole_i) )
    return R

def get_Potapov_vecs(T,poles):
    '''
    Given a transfer function T and some poles, compute the residues about the
    poles and generate the eigenvectors to use for constructing the projectors
    in the Blaschke-Potapov factorization.
    '''
    N = T(0).shape[0]
    found_vecs = []
    for pole in poles:
        L = (la.inv(Potapov_prod(pole,poles,found_vecs,N)) *
            f.limit(lambda z: (z-pole)*T(z),pole) ) ## Current bottleneck O(n^2).
        [eigvals,eigvecs] = la.eig(L)
        index = np.argmax(map(abs,eigvals))
        big_vec = np.asmatrix(eigvecs[:,index])
        found_vecs.append(big_vec)
    return found_vecs

def get_Potapov(T,poles,found_vecs):
    '''
    Given a transfer function T and some poles, generate the Blaschke-Potapov
    product to reconstruct or approximate T, assuming that T can be represented
    by the Blaschke-Potapov product with the given poles. Also match the values
    of the functions at zero.

    If T is a Blaschke-Potapov function and the the given poles are the only poles,
    then T will be reconstructed.

    In general, there is possibly an analytic term that is not captured by using
    a Blaschke-Potapov approximation.

    Args:
        T (matrix-valued function): A given meromorphic function

        poles (a list of complex valued numbers): The given poles of T

        vecs (list of complex-valued matrices): The eigenvectors corresponding to
        the orthogonal projectors of the Potapov product.

    Returns:
        A matrix-valued function equation to T at z=0 and approximating T
        using a Potapov product generated by its poles and residues.
    '''
    N = T(0).shape[0]
    return lambda z: T(0)*Potapov_prod(0,poles,found_vecs,N).H*\
        Potapov_prod(z,poles,found_vecs,N)

def prod(z,U,eigenvectors,eigenvalues):
    '''
    Return the Blaschke-Potapov product with the given eigenvalues and
    eigenvectors and constant unitary factor U evaluated at z.

    Args:
        z (complex number): where product is evaluated

        U (complex-valued matrix): A unitary matrix

        eigenvectors(list of complex-valued matrices): eigenvectors to use

        eigenvalues(list of complex numebrs): eigenvalues to use

    Returns:
        A complex-valued matrix equal to the Potapov product evaluated at z.

    '''
    if eigenvectors==[] or eigenvalues == []:
        return U
    else:
        vec = eigenvectors[-1]
        val = eigenvalues[-1]
        N = U.shape[0]
        return prod(z,U,eigenvectors[:-1],eigenvalues[:-1])*\
            (np.eye(N) - vec*vec.H + vec*vec.H*(z+val.conjugate())/(z-val))

def finite_transfer_function(U,eigenvectors,eigenvalues):
    '''
    Give a rational Blaschke-Potapov product of z with the given
    eigenvalues and eigenvectors and constant unitary factor U.

    Args:
        U (complex-valued matrix): A unitary matrix.

        eigenvectors(list of complex-valued matrices): eigenvectors to use

        eigenvalues(list of complex numebrs): eigenvalues to use

    Returns:
        A function that takes a complex number and returns the Potapov product
        evaluated at that number.

    '''
    return lambda z: prod(z,U,eigenvectors,eigenvalues)

def normalize(vec):
    '''
    Normalize a vector.

    Args:
        vec (complex-valued matrix): a vector

    Returns:
        The normalized vector.

    '''
    return vec / la.norm(vec)

def estimate_D(A,B,C,T,z):
    r'''
    Estimate the scattering matrix S=D using the ABC matrices
    the transfer function T at a frequency :math:`z = i \omega`.

    Try to satisfy
    :math:`T(z) = D + C(zI-A)^{-1}B`

    Args:
        A,B,C (matrices): The A,B, and C matrices of the
        state-space representation

        T (matrix-valued function): The input/output function
        to estimate

        z (complex number): the location at which the scattering
        matrix will be estimated

    Returns:
        The estimated S=D scaterring matrix based on the value of
        the function T and the ABC matrices.

    '''
    N = np.shape(A)[0]
    return T(z)+C*la.inv(A-z*np.eye(N))*B

def get_ABCD(val, vec):
    '''
    Make the ABCD model of a single Potapov factor given some eigenvalue
    and eigenvector.

    The ABCD model can be used to obtain the dynamics of a linear system.

    Args:
        val (complex number): an eigenvalue

        vec (complex-valued matrix): an eigenvector

        sym (optiona[boolean]): Modify :math:`B` and :math:`C` so that :math:`B = C.H`.

    Returns:
        A list [A,B,C,D] of four matrices representing the ABCD model.

    '''
    N = vec.shape[0]
    q = np.sqrt( -(val+val.conjugate()) )
    return [val*vec.H*vec, -q*vec.H, q*vec, np.eye(N)]

def get_Potapov_ABCD(poles,vecs,T=None,z=None):
    '''
    Combine the ABCD models for the different degrees of freedom.

    Args:
        val (a list of complex numbers): given eigenvalues

        vec (a list of complex-valued matrices): given eigenvectors

    Returns:
        A list [A,B,C,D] of four matrices representing the ABCD model.

    '''
    if min(len(poles),len(vecs)) < 1:
        print "Emptry list into get_Potapov_ABCD"
    elif min(len(poles),len(vecs)) == 1:
        return get_ABCD(poles[0],vecs[0])
    else:
        [A1,B1,C1,D1] = get_Potapov_ABCD(poles[1:], vecs[1:])
        [A2,B2,C2,D2] = get_ABCD(poles[0],vecs[0])

        O = np.zeros((A1.shape[0],A2.shape[1]))
        A_first_row_block =  np.hstack((A1,O))
        A_second_row_block = np.hstack((B2 * C1, A2))
        A = np.vstack((A_first_row_block,A_second_row_block))
        B = np.vstack(( B1, B2*D1))
        C = np.hstack(( D2*C1, C2))
        if T != None and z != None:
            D = estimate_D(A,B,C,T,z)
        else:
            D = D2*D1
        return [A,B,C,D]
