/**
 * Created by nishant on 2/13/15.
 */
public class CosineRunner {

    public static void main(String ar[]) throws Exception{
        if(ar.length<1){
            System.out.println("too few paramters");
            System.exit(-1);
        }
        CosineSim cs = new CosineSim(ar[0]);
        cs.calculatePairwiseSimilarity();
        //cs.test();
        cs.closeConnection();
    }
}
