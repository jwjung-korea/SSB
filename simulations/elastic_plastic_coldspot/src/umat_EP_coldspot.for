************************************************************************
C     FeFpFg UMAT for modeling plating/stripping of lithium
C     Sooraj Narayan and Lallit Anand
C     January 2019. Implemented in Abaqus 6.17
************************************************************************
      subroutine umat(stress,statev,ddsdde,sse,spd,scd,
     + rpl,ddsddt,drplde,drpldt,
     + stran,dstran,time,dtime,temp,dtemp,predef,dpred,cmname,
     + ndi,nshr,ntens,nstatv,props,nprops,coords,drot,pnewdt,
     + celent,dfgrd0,dfgrd1,noel,npt,layer,kspt,kstep,kinc)
C
      include 'aba_param.inc'
C
      dimension stress(ntens),statev(nstatv),
     + ddsdde(ntens,ntens),ddsddt(ntens),drplde(ntens),
     + stran(ntens),dstran(ntens),time(2),predef(1),dpred(1),
     + props(nprops),coords(3),drot(3,3),dfgrd0(3,3),dfgrd1(3,3)
C
      character*80 cmname
      integer i,j,k,l
      real*8 Iden(3,3),F_t(3,3),F_tau(3,3),Fp_t(3,3),Fp_tau(3,3)
      real*8 Fg_t(3,3),Fg_tau(3,3),T_tau(3,3),TK_tau(3,3),TK_per(3,3)
      real*8 MatTan(3,3,3,3),nuP_t,nuP_tau,S_t,S_tau,Y_t,Y_tau
      real*8 gBarP_t,gBarP_tau,eBarP_t,eBarP_tau,c_t,c_tau
      real*8 Gshear,Kbulk,plasticwork,detF_tau,detF_per,dE,perM(3,3)
      real*8 F_per(3,3),T_per(3,3),eBarLmt,umeror
      real*8 Eyoung,poisson,Y0,H0,Ysat,ahard,Omega,alpha1,alpha2,alpha3
C
      parameter(zero=0.d0,one=1.d0,two=2.d0,three=3.d0,half=0.5d0,
     +     root_three=1.732050807568877d0)
C
      Eyoung  = props(1)
      poisson = props(2)
      Y0      = props(3)
      H0      = props(4)
      Ysat    = props(5)
      ahard   = props(6)
      Omega   = props(7)
      alpha1  = props(8)
      alpha2  = props(9)
      alpha3  = props(10)
C
      Gshear = Eyoung/(two*(one+poisson))
      Kbulk  = Eyoung/(three*(one-two*poisson))
      ddsdde = zero   
      call onem(Iden)
      F_t = dfgrd0
      F_tau = dfgrd1
C
      if(time(2).eq.zero) then
         Fp_t      = Iden
         nuP_t     = zero
         S_t       = Y0/root_three
         Y_t       = Y0
         gBarP_t   = zero
         eBarP_t   = zero
         c_t       = zero
         Fg_t      = Iden 
      else
         Fp_t(1,1) = statev(1)
         Fp_t(2,2) = statev(2)
         Fp_t(3,3) = statev(3)
         Fp_t(2,3) = statev(4)
         Fp_t(3,2) = statev(5)
         Fp_t(1,3) = statev(6)
         Fp_t(3,1) = statev(7)
         Fp_t(1,2) = statev(8)
         Fp_t(2,1) = statev(9)
         nuP_t     = statev(10)
         S_t       = statev(11)
         Y_t       = statev(12)
         gBarP_t   = statev(13)
         eBarP_t   = statev(14)
         c_t       = statev(15)
         Fg_t(1,1) = statev(16)
         Fg_t(2,2) = statev(17)
         Fg_t(3,3) = statev(18)
         Fg_t(2,3) = statev(19)
         Fg_t(3,2) = statev(20)
         Fg_t(1,3) = statev(21)
         Fg_t(3,1) = statev(22)
         Fg_t(1,2) = statev(23)
         Fg_t(2,1) = statev(24)
      endif
C
      call integ(props,nprops,dtime,coords,cmname,time(2),
     +     F_t,F_tau,Fp_t,Fg_t,nuP_t,S_t,Y_t,gBarP_t,eBarP_t,c_t,
     +     Fp_tau,Fg_tau,nuP_tau,S_tau,Y_tau,gBarP_tau,eBarP_tau,c_tau,
     +     T_tau,plasticwork)
C
      statev(1)  = Fp_tau(1,1)
      statev(2)  = Fp_tau(2,2)
      statev(3)  = Fp_tau(3,3)
      statev(4)  = Fp_tau(2,3)
      statev(5)  = Fp_tau(3,2)
      statev(6)  = Fp_tau(1,3)
      statev(7)  = Fp_tau(3,1)
      statev(8)  = Fp_tau(1,2)
      statev(9)  = Fp_tau(2,1)
      statev(10) = nuP_tau
      statev(11) = S_tau 
      statev(12) = Y_tau       
      statev(13) = gBarP_tau
      statev(14) = eBarP_tau 
      statev(15) = c_tau
      statev(16) = Fg_tau(1,1)
      statev(17) = Fg_tau(2,2)
      statev(18) = Fg_tau(3,3)
      statev(19) = Fg_tau(2,3)
      statev(20) = Fg_tau(3,2)
      statev(21) = Fg_tau(1,3)
      statev(22) = Fg_tau(3,1)
      statev(23) = Fg_tau(1,2)
      statev(24) = Fg_tau(2,1)
C
      eBarLmt=0.02D0
      umeror = dabs((eBarP_tau - eBarP_t)/eBarLmt)
      if(umeror.le.half) then
         pnewdt = 1.5d0
      elseif((umeror.gt.half).and.(umeror.le.0.8d0)) then
         pnewdt = 1.25d0
      elseif((umeror.gt.0.8d0).and.(umeror.le.1.25d0)) then
         pnewdt = 0.75d0
      else
         pnewdt = half
      endif
C
      if(ntens.eq.6) then
         stress(1) = T_tau(1,1)
         stress(2) = T_tau(2,2)
         stress(3) = T_tau(3,3)
         stress(4) = T_tau(1,2)
         stress(5) = T_tau(1,3)
         stress(6) = T_tau(2,3)
      elseif(ntens.eq.4) then
         stress(1) = T_tau(1,1)
         stress(2) = T_tau(2,2)
         stress(3) = T_tau(3,3)
         stress(4) = T_tau(1,2)
      endif
C
      rpl = plasticwork         
      MatTan = zero
      call mdet(F_tau,detF_tau)
      TK_tau = detF_tau*T_tau         
      dE = 1.d-7
      do k=1,3
        do l=1,3              
            perM = zero
            perM(k,l) = one
            perM = (dE/two)*(perM + transpose(perM))
            F_per = F_tau + matmul(perM,F_t)
            call integ(props,nprops,dtime,coords,cmname,time(2),
     +       F_t,F_per,Fp_t,Fg_t,nuP_t,S_t,Y_t,gBarP_t,eBarP_t,c_t,
     +       Fp_tau,Fg_tau,nuP_tau,S_tau,Y_tau,gBarP_tau,eBarP_tau,c_tau,
     +       T_per,plasticwork)
            call mdet(F_per,detF_per)
            TK_per = detF_per*T_per
            do i=1,3
              do j=1,3
               MatTan(i,j,k,l) = (TK_per(i,j) -TK_tau(i,j))/dE
              enddo
            enddo
        enddo
      enddo
      MatTan = MatTan / detF_tau
      if(ntens.eq.6) then
          call jac3D(MatTan,ddsdde)
      elseif(ntens.eq.4) then
          call jac2D(MatTan,ddsdde)
      endif      
      return
      end subroutine umat
C
      subroutine integ(props,nprops,dtime,coords,cmname,step_time,
     +     F_t,F_tau,Fp_t,Fg_t,nuP_t,S_t,Y_t,gBarP_t,eBarP_t,c_t,
     +     Fp_tau,Fg_tau,nuP_tau,S_tau,Y_tau,gBarP_tau,eBarP_tau,c_tau,
     +     T_tau,plasticwork)
      include 'aba_param.inc'
      integer i,j,k,l,nprops
      character*80 cmname
      real*8 coords(3),step_time,props(nprops),dtime,F_t(3,3),F_tau(3,3)
      real*8 Fp_t(3,3),Fp_tau(3,3),nuP_t,Fg_t(3,3),gBarP_t,gBarP_tau
      real*8 S_tau,S_t,nuP_tau,T_tau(3,3),plasticwork,Iden(3,3)
      real*8 Fi_tr(3,3),Fi_tr_inv(3,3),Fe_tr(3,3),Re_tr(3,3),Ue_tr(3,3)
      real*8 Ee_tr(3,3),trEe_tr,Ee0_tr(3,3),Me_tr(3,3),Me0_tr(3,3)
      real*8 tauBar_tr,Np(3,3),detF_tau,detFg_tau,lambda_g1,lambda_g2
      real*8 lambda_g3,Fg_tau(3,3),Fi_tau(3,3),Fi_tau_inv(3,3),Fe_tau(3,3)
      real*8 Re_tau(3,3),Ue_tau(3,3),Ee_tau(3,3),Ee_tau_dev(3,3),trEe_tau
      real*8 Me_tau(3,3),Y_t,Y_tau,eBarP_t,eBarP_tau,H_t,dGamma,detFe_tau
      real*8 Eyoung,poisson,Y0,H0,Ysat,ahard,Omega,alpha1,alpha2,alpha3,cdot,cdot0        
      real*8 Gshear,Kbulk,Stilde,fac,Hsign,Dp_eig(3),Dp_vec(3,3),expdtDp(3,3)
      real*8 c_t,c_tau,tmp,Dp_tau(3,3)
      parameter(zero=0.d0,one=1.d0,two=2.d0,three=3.d0,half=0.5d0,
     +     root_three=1.732050807568877d0)
      Eyoung  = props(1)
      poisson = props(2)
      Y0      = props(3)
      H0      = props(4)
      Ysat    = props(5)
      ahard   = props(6)
      Omega   = props(7)
      alpha1  = props(8)
      alpha2  = props(9)
      alpha3  = props(10)
      cdot    = props(11)
      Gshear = Eyoung/(two*(one+poisson))
      Kbulk  = Eyoung/(three*(one-two*poisson))
      call onem(Iden)
      if ((props(11).gt.0.1d0).or.(cmname(1:10).eq.'LITHIUM_IP')) then
          cdot0 = 103.643d0
          if(mod(int(step_time/2160.d0),2).ne.0) cdot0 = -cdot0
          if(coords(1).lt.8.5d0) then
              cdot = cdot0
          elseif(coords(1).ge.8.5d0 .and. coords(1).le.9.0d0) then
              cdot = cdot0 - (cdot0 - cdot0/10.d0)*(coords(1) - 8.5d0)/0.5d0
          elseif(coords(1).gt.9.0d0 .and. coords(1).lt.11.0d0) then
              cdot = cdot0/10.d0
          elseif(coords(1).ge.11.0d0 .and. coords(1).le.11.5d0) then
              cdot = cdot0/10.d0 + (cdot0 - cdot0/10.d0)*(coords(1) - 11.0d0)/0.5d0
          else
              cdot = cdot0
          endif
      else
          cdot = 0.d0
      endif
      c_tau = c_t + dtime*cdot
      if (c_tau.lt.zero) c_tau = zero
      detFg_tau = one + 1.3d-5*c_tau
      lambda_g1 = one + 0.d0*(detFg_tau - one)
      lambda_g2 = one + 1.d0*(detFg_tau - one)
      lambda_g3 = one + 0.d0*(detFg_tau - one)
      Fg_tau = zero
      Fg_tau(1,1) = lambda_g1
      Fg_tau(2,2) = lambda_g2
      Fg_tau(3,3) = lambda_g3
      Fi_tr = matmul(Fp_t,Fg_tau)   
      call m3inv(Fi_tr,Fi_tr_inv)
      Fe_tr = matmul(F_tau,Fi_tr_inv)
      call skinem(Fe_tr,Re_tr,Ue_tr,Ee_tr)
      trEe_tr = Ee_tr(1,1) + Ee_tr(2,2) + Ee_tr(3,3)
      Ee0_tr = Ee_tr - (one/three)*trEe_tr*Iden
      call mdet(F_tau,detF_tau)
      detFe_tau = detF_tau/detFg_tau
      trEe_tau = dlog(detFe_tau)
      Me_tr = two*Gshear*Ee0_tr + Kbulk*(trEe_tau)*Iden
      Me0_tr = Me_tr - (one/three)*(Me_tr(1,1)+Me_tr(2,2)+Me_tr(3,3))*Iden
      tauBar_tr = dsqrt(one/two)*dsqrt(sum(Me0_tr*Me0_tr))
      if(tauBar_tr.gt.zero) then
         Np = Me0_tr/(dsqrt(two)*tauBar_tr)
      else
         Np = zero
      endif
      if(tauBar_tr.le.S_t) then
         nuP_tau = zero
         H_t = zero
      else
         H_t    = H0/three
         dGamma = (tauBar_tr - S_t) / (Gshear + H_t)
         nuP_tau = max(dGamma / dtime, zero)
      endif
      gBarP_tau = gBarP_t + dtime*nuP_tau
      eBarP_tau = gBarP_tau/root_three
      Dp_tau = (one/dsqrt(two))*nuP_tau*Np
      if(nuP_tau.le.zero) then
         Fp_tau = Fp_t
      else
         call spectral(dtime*Dp_tau,Dp_eig,Dp_vec)
         expdtDp = zero
         expdtDp(1,1) = dexp(Dp_eig(1))
         expdtDp(2,2) = dexp(Dp_eig(2))
         expdtDp(3,3) = dexp(Dp_eig(3))
         expdtDp = matmul(matmul(Dp_vec,expdtDp),transpose(Dp_vec))
         Fp_tau = matmul(expdtDp,Fp_t)
      endif
      Fi_tau = matmul(Fp_tau,Fg_tau)            
      call m3inv(Fi_tau,Fi_tau_inv)
      Fe_tau = matmul(F_tau,Fi_tau_inv)
      call skinem(Fe_tau,Re_tau,Ue_tau,Ee_tau)
      trEe_tau = Ee_tau(1,1) + Ee_tau(2,2) + Ee_tau(3,3)
      Ee_tau_dev = Ee_tau - (one/three)*trEe_tau*Iden
      Me_tau = two*Gshear*Ee_tau_dev + Kbulk*(trEe_tau)*Iden      
      T_tau = matmul(Re_tau,matmul(Me_tau,transpose(Re_tau)))/detFe_tau
      S_tau = S_t + H_t*dtime*nuP_tau      
      Y_tau = root_three*S_tau
      plasticwork = S_tau*nuP_tau
      return
      end subroutine integ
C
      subroutine spectral(A,eig,vec)
      include 'aba_param.inc'
      real*8 A(3,3),eig(3),vec(3,3)
      integer nrot
      call jacobi(A,3,3,eig,vec,nrot)
      return
      end subroutine spectral
C
      SUBROUTINE JACOBI(A,N,NP,D,V,NROT)
      include 'aba_param.inc'
      PARAMETER (NMAX=100)
      DIMENSION A(NP,NP),D(NP),V(NP,NP),B(NMAX),Z(NMAX)
      DO 12 IP=1,N
        DO 11 IQ=1,N
          V(IP,IQ)=0.0D0
11      CONTINUE
        V(IP,IP)=1.0D0
12    CONTINUE
      DO 13 IP=1,N
        B(IP)=A(IP,IP)
        D(IP)=B(IP)
        Z(IP)=0.0D0
13    CONTINUE
      NROT=0
      DO 24 I=1,50
        SM=0.0D0
        DO 15 IP=1,N-1
          DO 14 IQ=IP+1,N
            SM=SM+DABS(A(IP,IQ))
14        CONTINUE
15      CONTINUE
        IF(SM.EQ.0.0D0) RETURN
        IF(I.LT.4) THEN
          TRESH=0.2D0*SM/N**2
        ELSE
          TRESH=0.0D0
        ENDIF
        DO 22 IP=1,N-1
          DO 21 IQ=IP+1,N
            G=100.0D0*DABS(A(IP,IQ))
            IF((I.GT.4).AND.(DABS(D(IP))+G.EQ.DABS(D(IP)))
     +         .AND.(DABS(D(IQ))+G.EQ.DABS(D(IQ)))) THEN
              A(IP,IQ)=0.0D0
            ELSE IF(DABS(A(IP,IQ)).GT.TRESH) THEN
              HH=D(IQ)-D(IP)
              IF(DABS(HH)+G.EQ.DABS(HH)) THEN
                T=A(IP,IQ)/HH
              ELSE
                THETA=0.5D0*HH/A(IP,IQ)
                T=1.0D0/(DABS(THETA)+DSQRT(1.0D0+THETA**2))
                IF(THETA.LT.0.0D0) T=-T
              ENDIF
              C=1.0D0/DSQRT(1.D0+T**2)
              S=T*C
              TAU=S/(1.0D0+C)
              HH=T*A(IP,IQ)
              Z(IP)=Z(IP)-HH
              Z(IQ)=Z(IQ)+HH
              D(IP)=D(IP)-HH
              D(IQ)=D(IQ)+HH
              A(IP,IQ)=0.0D0
              DO 16 J=1,IP-1
                G=A(J,IP)
                HH=A(J,IQ)
                A(J,IP)=G-S*(HH+G*TAU)
                A(J,IQ)=HH+S*(G-HH*TAU)
16            CONTINUE
              DO 17 J=IP+1,IQ-1
                G=A(IP,J)
                HH=A(J,IQ)
                A(IP,J)=G-S*(HH+G*TAU)
                A(J,IQ)=HH+S*(G-HH*TAU)
17            CONTINUE
              DO 18 J=IQ+1,N
                G=A(IP,J)
                HH=A(IQ,J)
                A(IP,J)=G-S*(HH+G*TAU)
                A(IQ,J)=HH+S*(G-HH*TAU)
18            CONTINUE
              DO 19 J=1,N
                G=V(J,IP)
                HH=V(J,IQ)
                V(J,IP)=G-S*(HH+G*TAU)
                V(J,IQ)=HH+S*(G-HH*TAU)
19            CONTINUE
              NROT=NROT+1
            ENDIF
21        CONTINUE
22      CONTINUE
        DO 23 IP=1,N
          B(IP)=B(IP)+Z(IP)
          D(IP)=B(IP)
          Z(IP)=0.0D0
23      CONTINUE
24    CONTINUE
      RETURN
      END SUBROUTINE JACOBI
C
      subroutine mdet(A,detA)
      include 'aba_param.inc'
      real*8 A(3,3),detA
      detA = A(1,1)*A(2,2)*A(3,3) + A(1,2)*A(2,3)*A(3,1) + 
     +       A(1,3)*A(2,1)*A(3,2) - A(1,3)*A(2,2)*A(3,1) - 
     +       A(1,2)*A(2,1)*A(3,3) - A(1,1)*A(2,3)*A(3,2)
      return
      end subroutine mdet
C
      subroutine m3inv(A,Ainv)
      include 'aba_param.inc'
      real*8 A(3,3),Ainv(3,3),detA
      call mdet(A,detA)
      Ainv(1,1) = (A(2,2)*A(3,3) - A(2,3)*A(3,2))/detA
      Ainv(1,2) = (A(1,3)*A(3,2) - A(1,2)*A(3,3))/detA
      Ainv(1,3) = (A(1,2)*A(2,3) - A(1,3)*A(2,2))/detA
      Ainv(2,1) = (A(2,3)*A(3,1) - A(2,1)*A(3,3))/detA
      Ainv(2,2) = (A(1,1)*A(3,3) - A(1,3)*A(3,1))/detA
      Ainv(2,3) = (A(1,3)*A(2,1) - A(1,1)*A(2,3))/detA
      Ainv(3,1) = (A(2,1)*A(3,2) - A(2,2)*A(3,1))/detA
      Ainv(3,2) = (A(1,2)*A(3,1) - A(1,1)*A(3,2))/detA
      Ainv(3,3) = (A(1,1)*A(2,2) - A(1,2)*A(2,1))/detA
      return
      end subroutine m3inv
C
      subroutine onem(A)
      include 'aba_param.inc'
      real*8 A(3,3)
      A(1,1) = 1.d0
      A(1,2) = 0.d0
      A(1,3) = 0.d0
      A(2,1) = 0.d0
      A(2,2) = 1.d0
      A(2,3) = 0.d0
      A(3,1) = 0.d0
      A(3,2) = 0.d0
      A(3,3) = 1.d0
      return
      end subroutine onem
C
      subroutine skinem(F,R,U,E)
      include 'aba_param.inc'
      real*8 F(3,3),R(3,3),U(3,3),E(3,3),C(3,3),eig(3),vec(3,3),Ueig(3)
      C = matmul(transpose(F),F)
      call spectral(C,eig,vec)
      Ueig(1) = dsqrt(max(eig(1),1.d-14))
      Ueig(2) = dsqrt(max(eig(2),1.d-14))
      Ueig(3) = dsqrt(max(eig(3),1.d-14))
      U = 0.d0
      U(1,1) = Ueig(1)
      U(2,2) = Ueig(2)
      U(3,3) = Ueig(3)
      U = matmul(matmul(vec,U),transpose(vec))
      E = 0.d0
      E(1,1) = dlog(Ueig(1))
      E(2,2) = dlog(Ueig(2))
      E(3,3) = dlog(Ueig(3))
      E = matmul(matmul(vec,E),transpose(vec))
      call m3inv(U,C)
      R = matmul(F,C)
      return
      end subroutine skinem
C
      subroutine jac2D(SpTanMod,ddsdde)
      include 'aba_param.inc'
      real*8 SpTanMod(3,3,3,3),ddsdde(4,4)
      ddsdde(1,1) = SpTanMod(1,1,1,1)
      ddsdde(1,2) = SpTanMod(1,1,2,2)
      ddsdde(1,3) = SpTanMod(1,1,3,3)
      ddsdde(1,4) = SpTanMod(1,1,1,2)
      ddsdde(2,1) = SpTanMod(2,2,1,1)
      ddsdde(2,2) = SpTanMod(2,2,2,2)
      ddsdde(2,3) = SpTanMod(2,2,3,3)
      ddsdde(2,4) = SpTanMod(2,2,1,2)
      ddsdde(3,1) = SpTanMod(3,3,1,1)
      ddsdde(3,2) = SpTanMod(3,3,2,2)
      ddsdde(3,3) = SpTanMod(3,3,3,3)
      ddsdde(3,4) = SpTanMod(3,3,1,2)
      ddsdde(4,1) = SpTanMod(1,2,1,1)
      ddsdde(4,2) = SpTanMod(1,2,2,2)
      ddsdde(4,3) = SpTanMod(1,2,3,3)
      ddsdde(4,4) = SpTanMod(1,2,1,2)
      return
      end subroutine jac2D
C
      subroutine jac3D(SpTanMod,ddsdde)
      include 'aba_param.inc'
      real*8 SpTanMod(3,3,3,3),ddsdde(6,6)
      ddsdde(1,1) = SpTanMod(1,1,1,1)
      ddsdde(1,2) = SpTanMod(1,1,2,2)
      ddsdde(1,3) = SpTanMod(1,1,3,3)
      ddsdde(1,4) = SpTanMod(1,1,1,2)
      ddsdde(1,5) = SpTanMod(1,1,1,3)
      ddsdde(1,6) = SpTanMod(1,1,2,3)
      ddsdde(2,1) = SpTanMod(2,2,1,1)
      ddsdde(2,2) = SpTanMod(2,2,2,2)
      ddsdde(2,3) = SpTanMod(2,2,3,3)
      ddsdde(2,4) = SpTanMod(2,2,1,2)
      ddsdde(2,5) = SpTanMod(2,2,1,3)
      ddsdde(2,6) = SpTanMod(2,2,2,3)
      ddsdde(3,1) = SpTanMod(3,3,1,1)
      ddsdde(3,2) = SpTanMod(3,3,2,2)
      ddsdde(3,3) = SpTanMod(3,3,3,3)
      ddsdde(3,4) = SpTanMod(3,3,1,2)
      ddsdde(3,5) = SpTanMod(3,3,1,3)
      ddsdde(3,6) = SpTanMod(3,3,2,3)
      ddsdde(4,1) = SpTanMod(1,2,1,1)
      ddsdde(4,2) = SpTanMod(1,2,2,2)
      ddsdde(4,3) = SpTanMod(1,2,3,3)
      ddsdde(4,4) = SpTanMod(1,2,1,2)
      ddsdde(4,5) = SpTanMod(1,2,1,3)
      ddsdde(4,6) = SpTanMod(1,2,2,3)
      ddsdde(5,1) = SpTanMod(1,3,1,1)
      ddsdde(5,2) = SpTanMod(1,3,2,2)
      ddsdde(5,3) = SpTanMod(1,3,3,3)
      ddsdde(5,4) = SpTanMod(1,3,1,2)
      ddsdde(5,5) = SpTanMod(1,3,1,3)
      ddsdde(5,6) = SpTanMod(1,3,2,3)
      ddsdde(6,1) = SpTanMod(2,3,1,1)
      ddsdde(6,2) = SpTanMod(2,3,2,2)
      ddsdde(6,3) = SpTanMod(2,3,3,3)
      ddsdde(6,4) = SpTanMod(2,3,1,2)
      ddsdde(6,5) = SpTanMod(2,3,1,3)
      ddsdde(6,6) = SpTanMod(2,3,2,3)
      return
      end subroutine jac3D
