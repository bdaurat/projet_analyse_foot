// Online C compiler to run C program online
#include <stdio.h>
#include <math.h>
#include <stdlib.h>

void affiche_mat(double *A, int n){
    for (int i = 0; i<n; i++){
        printf("%d",A[i]);
    }
}

void affiche_vec(double *V, int m){
    for (int i = 0; i<m; i++){
        printf("%d",V[i]);
    }
}

double max_colonnes(double *A, int i, int n){
    double max = 0;
    for (int j = 0; j<n; j++){
        if (max < fabs(A[j*n + j])) {
            max = fabs(A[j*n + i]);
        }
    }
    return max;
}

void echange(double *A, double *b, int L1, int L2, int n){
    double tempb = b[L1];
    b[L1] = b[L2];
    b[L2] = tempb;
    for (int i = 0; i<n ; i++){
        double tempA = A[L1*n + i];
        A[L1*n + i] = A[L2*n + i];
        A[L2*n + i] = tempA;
    }
}

void normalize(double *A, int i, int j, int n){
    double pivot  = A[i*n + j];
    if (pivot == 0.0){
        printf("rien à faire, pivot nul");
    }
    else {
        for (int k = 0; k<n ; k++){
            A[i*n+k] = (A[i*n+k])/pivot;
        }
    }
}

void mult_ligne(double *A, double facteur, int i, int n){
    for (int k = 0; k<n ; k++){
        A[i*n+k] = (A[i*n+k])*facteur;}
}

void pivot(double *A, double *b, int n) {
    for(int i = 0; i < n; i++) {
        normalize(A, i, i, n);
        b[i] = b[i] / A[i*n + i];
        for(int j = i+1; j < n; j++) {
            double coeff = A[j*n + i];
            for(int k = i; k < n; k++)
                A[j*n + k] -= coeff * A[i*n + k];

            b[j] -= coeff * b[i];
        }
    }
}

void gauss(double *A, double *b, double *x, int n){
    pivot(A,b,n);
    for(int i = n-1; i >= 0; i--){
        x[i] = b[i];
        for(int j = i+1; j < n; j++){
            x[i] -= A[i*n + j] * x[j];
        }
    }
}

int main() {
    int n = 4;
    double *A = malloc(n*n*sizeof(double));
    double *b = malloc(n*sizeof(double));
    double *x = malloc(n*sizeof(double));
    double tempb[4] = {1,2,3,3};
    double tempA[16] = {1,3,4,1,2,4,3,4,1,1,2,5,1,4,5,2};
    for(int i=0; i<n*n; i++) A[i] = tempA[i];
    for(int i=0; i<n; i++) b[i] = tempb[i];

    gauss(A,b,x,n);
    for(int i=0; i<n; i++)
        printf("x[%d] = %lf\n", i, x[i]);



    free(A);
    free(b);
    free(x);
    return 0;
}
